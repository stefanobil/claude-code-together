import time
import schedule
from rich.console import Console
from rich.table import Table
from config import TRADING_CONFIG
from data_fetcher import DataFetcher
from indicators import add_all_indicators
from strategy import check_buy_signal, check_sell_signal, check_market_structure_trend
from ml_model import MLPredictor
from risk_manager import calculate_smc_sl_tp
from notifier import send_telegram_alert
from logger_manager import log_trade, log_error, get_performance_summary
try:
    from macro_analyst import macro_analyst
except ImportError:
    macro_analyst = None

console = Console()
fetcher = DataFetcher()
ml = MLPredictor()

# Statut Global pour éviter le spam News
news_alert_sent = False

# Gestion de l'état asynchrone V6.0 (Hedge + Re-entry + Correlation)
states = {sym: {
    'positions': {
        'LONG': {'active': False, 'entry': 0.0, 'sl': 0.0, 'tp': 0.0, 'risk': 0.0, 'be': False, 'trailing': False, 'hi': 0.0, 'pos_size_asset': 0.0},
        'SHORT': {'active': False, 'entry': 0.0, 'sl': 0.0, 'tp': 0.0, 'risk': 0.0, 'be': False, 'trailing': False, 'lo': 9999999.0, 'pos_size_asset': 0.0}
    },
    'consecutive_losses': 0,
    'freeze_until': 0.0,
    'reentry_count': { 'LONG': 0, 'SHORT': 0 } # V6.0 : Suivi des tentatives
} for sym in TRADING_CONFIG['symbols']}

def process_symbol(symbol: str, news_danger: bool, btc_trend: str):
    """Moteur Central V6.0 : Hedge + BTC Correlation + Sniper Re-entry."""
    st = states[symbol]
    
    if time.time() < st['freeze_until']:
        # Doit retourner 6 valeurs
        return False, 0.0, 0.0, 0.0, "NEUTRE", {}
    
    df_1h = fetcher.get_historical_data(symbol, TRADING_CONFIG['timeframe'])
    df_macro = fetcher.get_historical_data(symbol, TRADING_CONFIG['macro_timeframe'], limit=800)
    derivatives = fetcher.get_derivatives_data(symbol) 
    
    if df_1h.empty:
        # Doit retourner 6 valeurs
        return False, 0.0, 0.0, 0.0, "NEUTRE", derivatives
    df_1h = add_all_indicators(df_1h)
    if not df_macro.empty: df_macro = add_all_indicators(df_macro)
    
    current_price = df_1h.iloc[-1]['close']
    current_atr = df_1h.iloc[-1]['atr']
    current_adx = df_1h.iloc[-1].get('adx', 0.0)
    
    if not ml.is_trained: ml.train(df_1h)
    ia_prob = ml.predict_next_candle(df_1h)['probability'] 
    
    # Détermination de la tendance brute V6.3.3
    from strategy import check_market_structure_trend
    trend = check_market_structure_trend(df_1h)
    
    # 1. GESTION DES ENTRÉES (Standard, Hedge & Re-entry)
    buy_cond = check_buy_signal(df_1h, df_macro, derivatives, btc_trend)
    sell_cond = check_sell_signal(df_1h, df_macro, derivatives, btc_trend)
    
    for side in ['LONG', 'SHORT']:
        pos = st['positions'][side]
        other_side = 'SHORT' if side == 'LONG' else 'LONG'
        other_pos = st['positions'][other_side]
        
        # Signal V6.0 (incluant BTC Filter + Delta)
        cond_dict = buy_cond if side == 'LONG' else sell_cond
        signal = cond_dict['signal']
        ob_level = cond_dict['ob_level']
        tp_target = cond_dict.get('tp_target', 0.0)
        
        # LOGIQUE HEDGE V4.2
        is_hedging = False
        if TRADING_CONFIG.get('hedge_mode_enabled') and other_pos['active'] and not pos['active']:
            threatened = abs(current_price - other_pos['sl']) < (current_atr * 1.5)
            flip = df_1h.iloc[-1].get('structure_flip_down' if other_side == 'LONG' else 'structure_flip_up', False)
            strong_trend = current_adx > TRADING_CONFIG.get('adx_min_strength', 20)
            if threatened and flip and strong_trend:
                is_hedging = True
                signal = True
                ob_level = current_price

        # LOGIQUE RE-ENTRY V6.0
        is_reentry = False
        if not pos['active'] and signal and st['reentry_count'][side] > 0:
            is_reentry = True

        if signal and not pos['active'] and not news_danger:
            # Filtre ADX Strict
            if current_adx < TRADING_CONFIG.get('adx_min_strength', 20):
                continue
                
            # LOGIQUE D'ALERTE ÉLITE V7.1 (70% Probabilité Min.)
            prob_final = ia_prob if side == 'LONG' else (1.0 - ia_prob)
            prob_pct = prob_final * 100
            
            if prob_pct < 70.0:
                # Log interne sans notification Telegram
                log_trade(symbol, side, f"REJECTED: Prob {prob_pct:.1f}%", current_price, 0, 0, 0, 0, f"LOW PROBABILITY: {prob_pct:.1f}%")
                continue

            sl, tp = calculate_smc_sl_tp(side, current_price, ob_level, current_atr, tp_target)
            risk_per_unit = abs(current_price - sl)
            
            # Simulation de Trade (Capital 300$, Risque 1%, Levier 3x)
            capital = 300.0
            risk_pct = 0.01
            leverage = 3
            risk_amount = capital * risk_pct  # 3.0$
            
            if risk_per_unit > 0:
                pos_size_asset = risk_amount / risk_per_unit
                pos_size_usd = pos_size_asset * current_price
                est_profit_usd = pos_size_asset * abs(tp - current_price)
                est_loss_usd = risk_amount
                profit_pct_capital = (est_profit_usd / capital) * 100
                loss_pct_capital = (est_loss_usd / capital) * 100
            else:
                pos_size_usd = 0; est_profit_usd = 0; est_loss_usd = 0; profit_pct_capital = 0; loss_pct_capital = 0

            # Construction du message Élite en Français
            emoji = "🚨" if side == 'LONG' else "🚨"
            direction_fr = "HAUSSE (LONG)" if side == 'LONG' else "BAISSE (SHORT)"
            type_trade = "🛡️ HEDGE" if is_hedging else ("🔫 RE-ENTRY" if is_reentry else "🚀 DIRECTIONNEL")
            
            msg = f"🚨 **ALERTE TRADE — {symbol} ({direction_fr})**\n\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "📊 **CONTEXTE MARCHÉ**\n"
            msg += f"• Tendance actuelle : {trend}\n"
            msg += f"• Confirmation : Structure {trend} confirmée sur {TRADING_CONFIG['timeframe']}\n"
            msg += f"• État : {'Volatil' if current_adx > 30 else 'Tendance saine' if current_adx > 20 else 'Consolidation'}\n\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "🧠 **CONFIRMATION SIGNAL IA**\n"
            msg += f"• Probabilité IA : {prob_pct:.1f}%\n"
            msg += f"• Force du Signal : {'Forte' if prob_pct > 80 else 'Modérée'}\n"
            msg += "• Confluences :\n"
            msg += f"  - Momentum Delta : {cond_dict.get('delta', 0.0)*100:+.1f}%\n"
            msg += f"  - Filtre Corrélation BTC : {btc_trend}\n"
            msg += f"  - Type d'exécution : {type_trade}\n\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "📈 **CONFIRMATIONS TECHNIQUES**\n"
            msg += f"• ADX : {current_adx:.1f} → {'Tendance forte' if current_adx > 25 else 'Tendance naissante'}\n"
            msg += f"• Structure : {trend} (Confirmed Alignment)\n"
            msg += f"• Momentum : {'Haussier' if side == 'LONG' else 'Baissier'}\n\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "💧 **DONNÉES SMART MONEY**\n"
            msg += f"• Zones de Liquidité : {cond_dict.get('liquidity_zone', 'N/A')}\n"
            msg += f"• Imbalance (FVG) : {cond_dict.get('fvg_detected', 'N/A')}\n"
            msg += f"• Order Flow / Delta : {'Pression Acheteuse' if side == 'LONG' else 'Pression Vendeuse'}\n\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "🎯 **CONFIGURATION DU TRADE**\n"
            msg += f"• Entrée : `{current_price:.5f}`\n"
            msg += f"• Stop Loss : `{sl:.5f}`\n"
            msg += f"• Take Profit : `{tp:.5f}`\n"
            msg += f"• Ratio R/R : 1:{abs(tp-current_price)/risk_per_unit:.1f}\n\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "⚠️ **RAPPEL GESTION DES RISQUES**\n"
            msg += "• Risque par trade : 1% maximum\n"
            msg += "• Ne pas surexposer (Levier 3x max)\n"
            msg += "• Respectez le Stop Loss sans exception\n"
            msg += "• Ignorez si les conditions changent brusquement\n\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "💰 **SIMULATION DE TRADE (PROFIL STÉPHANE)**\n"
            msg += f"• Capital : 300$\n"
            msg += f"• Levier : 3x\n"
            msg += f"• Taille Position : {pos_size_usd:.2f}$\n\n"
            msg += f"Si le TP est atteint :\n"
            msg += f"→ Profit Estimé : +{est_profit_usd:.2f}$ (+{profit_pct_capital:.1f}%)\n\n"
            msg += f"Si le SL est atteint :\n"
            msg += f"→ Perte Estimée : -{est_loss_usd:.2f}$ (-{loss_pct_capital:.1f}%)\n\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "🧭 **INSIGHT D'EXÉCUTION**\n"
            msg += f"• Configuration de type {'A+' if prob_pct > 80 and current_adx > 25 else 'B'}\n"
            msg += f"• Condition de succès : Maintien de la structure {trend}.\n"
            msg += f"• Invalidation : Cassure franche du niveau SL.\n\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            msg += "📡 **NOTE FINALE**\n"
            msg += "Monsieur Stéphane, la discipline surpasse l'intelligence. Suivez le plan, la précision forge la fortune.\n\n"
            msg += "Precision creates power. Execute like a professional, Mr Stéphane.\n"

            pos.update({
                'active': True, 'entry': current_price, 'sl': sl, 'tp': tp, 
                'risk': risk_per_unit, 'be': False, 'trailing': False,
                'hi': current_price, 'lo': current_price,
                'pos_size_asset': pos_size_asset
            })
            
            console.print(f"[bold cyan]{type_trade} : {side} {symbol}[/bold cyan]")
            send_telegram_alert(msg)

            # Audit Logging (Entry)
            log_trade(
                symbol=symbol,
                side=side,
                type_trade=type_trade,
                entry_price=current_price,
                exit_price=0.0,
                pnl_usd=0.0,
                pnl_pct=0.0,
                duration=0,
                reason=f"ENTRY: {type_trade} (Prob: {prob_pct:.1f}%)"
            )

    # 2. GESTION DES SORTIES
    for side in ['LONG', 'SHORT']:
        pos = st['positions'][side]
        if not pos['active']: continue
        
        r_val = pos['risk'] if pos['risk'] > 0 else current_price * 0.01
        hit_exit = False
        
        if side == 'LONG':
            if current_price > pos['hi']: pos['hi'] = current_price
            curr_r = (current_price - pos['entry']) / r_val
            if curr_r >= TRADING_CONFIG['break_even_at_r'] and not pos['be']:
                pos['sl'] = pos['entry']
                pos['be'] = True
                send_telegram_alert(f"🛡️ **SÉCURITÉ ACTIVÉE : {symbol} LONG**\nLe prix a atteint +{TRADING_CONFIG['break_even_at_r']}R. Le Stop-Loss est déplacé à l'entrée. \n*Trade désormais sans risque (Risk-Free) !* ✅")
                
            if curr_r >= TRADING_CONFIG['trailing_activation_r']:
                n_sl = pos['hi'] * (1 - TRADING_CONFIG['trailing_distance_pct'])
                if n_sl > pos['sl']: 
                    if not pos['trailing']:
                        send_telegram_alert(f"💰 **BÉNÉFICE VERROUILLÉ : {symbol} LONG**\nLe Trailing Stop est activé. Nous suivons la hausse pour maximiser le gain ! 📈")
                    pos['sl'] = n_sl
                    pos['trailing'] = True
            hit_exit = (current_price <= pos['sl']) or (current_price >= pos['tp'])
        else:
            if current_price < pos['lo']: pos['lo'] = current_price
            curr_r = (pos['entry'] - current_price) / r_val
            if curr_r >= TRADING_CONFIG['break_even_at_r'] and not pos['be']:
                pos['sl'] = pos['entry']
                pos['be'] = True
                send_telegram_alert(f"🛡️ **SÉCURITÉ ACTIVÉE : {symbol} SHORT**\nLe prix a atteint +{TRADING_CONFIG['break_even_at_r']}R. Le Stop-Loss est déplacé à l'entrée. \n*Trade désormais sans risque (Risk-Free) !* ✅")
                
            if curr_r >= TRADING_CONFIG['trailing_activation_r']:
                n_sl = pos['lo'] * (1 + TRADING_CONFIG['trailing_distance_pct'])
                if n_sl < pos['sl']: 
                    if not pos['trailing']:
                        send_telegram_alert(f"💰 **BÉNÉFICE VERROUILLÉ : {symbol} SHORT**\nLe Trailing Stop est activé. Nous suivons la baisse pour maximiser le gain ! 📉")
                    pos['sl'] = n_sl
                    pos['trailing'] = True
            hit_exit = (current_price >= pos['sl']) or (current_price <= pos['tp'])
            
        if hit_exit:
            win = (current_price > pos['entry'] if side == 'LONG' else current_price < pos['entry'])
            
            # Logique de Perte / Re-entry V6.0
            if not win and not pos['be']:
                # Est-ce qu'on autorise une ré-entrée ?
                if TRADING_CONFIG.get('reentry_allowed') and st['reentry_count'][side] < TRADING_CONFIG.get('reentry_max_attempts', 1):
                    st['reentry_count'][side] += 1
                    send_telegram_alert(f"🔫 **STOP HUNT DÉTECTÉ : {symbol} {side}**\nOn surveille la structure pour une ré-entrée (Tentative {st['reentry_count'][side]}).")
                else:
                    st['consecutive_losses'] += 1
                    st['reentry_count'][side] = 0 # Reset si on dépasse la limite
                    if st['consecutive_losses'] >= TRADING_CONFIG['consecutive_loss_limit']:
                        st['freeze_until'] = time.time() + (TRADING_CONFIG['freeze_duration_hours'] * 3600)
            else:
                st['consecutive_losses'] = 0
                st['reentry_count'][side] = 0 # Reset sur TP ou BE
                
            send_telegram_alert(f"🏁 *Sortie {side} {symbol}*")
            pos['active'] = False
            
            # Audit Logging (Exit)
            pnl_val = (current_price - pos['entry']) if side == 'LONG' else (pos['entry'] - current_price)
            pnl_pct = (pnl_val / pos['entry']) * 100
            # Calcul PnL USD Réel basé sur la taille d'entrée (V7.1 Patch)
            pnl_usd = pnl_val * pos['pos_size_asset']
            
            log_trade(
                symbol=symbol,
                side=side,
                type_trade="EXIT",
                entry_price=pos['entry'],
                exit_price=current_price,
                pnl_usd=pnl_usd,
                pnl_pct=pnl_pct,
                duration=0, # À calculer si nécessaire
                reason="HIT SL/TP"
            )

    # Retourne aussi la tendance brute pour affichage
    return any(p['active'] for p in st['positions'].values()), current_price, ia_prob, current_adx, trend, derivatives

def analyze_portfolio():
    global news_alert_sent
    console.print("\n[bold cyan]🏛️ V6.3.2 INSTITUTIONAL SMC ENGINE (Dual-Side High-Sec)...[/bold cyan]")
    
    # 1. Verification du Bouclier Anti-News
    news = fetcher.check_high_impact_news()
    if news:
        if not news_alert_sent:
            msg = "🚨 **ALERTE NEWS ÉCONOMIQUE US** : Protection du Capital Activée / Les nouvelles ouvertures de trades sont gelées temporairement."
            send_telegram_alert(msg)
            news_alert_sent = True
            
    # Briefing de 7h00 (Automatique)
    if macro_analyst:
        macro_analyst.check_and_send_briefing()

    if not news:
        if news_alert_sent:
            send_telegram_alert("📉 **FIN D'ALERTE NEWS** : Le marché s'est stabilisé. Le scanner reprend ses opérations normales.")
            news_alert_sent = False
        
    # 2. Status du Marché Global
    btc_t = fetcher.get_btc_trend()
    btc_color = "green" if btc_t == 'BULLISH' else ("red" if btc_t == 'BEARISH' else "yellow")
    console.print(f"[bold]Tendance Marché (BTC) : [/bold][{btc_color}]{btc_t}[/{btc_color}]")
    
    # 2.5 Affichage résumé Performance (Auditor)
    perf = get_performance_summary()
    if isinstance(perf, dict):
        pnl_total = perf.get('total_pnl_usd', 0.0)
        wr = perf.get('win_rate', 0.0)
        console.print(f"📊 [bold yellow]AUDIT PERFORMANCE[/bold yellow] | PnL Total: [green]{pnl_total:.2f}$[/green] | WinRate: [cyan]{wr:.1f}%[/cyan] | Trades: [white]{perf.get('total_trades',0)}[/white]\n")

    # 3. Construction du Dashboard Elite
    table = Table(title="💎 SMC QUANTITATIVE DASHBOARD", title_style="bold magenta", border_style="cyan")
    table.add_column("Paire", style="cyan", no_wrap=True)
    table.add_column("Statut Signal", justify="center")
    table.add_column("Prix Actuel", justify="right", style="white")
    table.add_column("IA Long/Short", justify="center", style="yellow")
    table.add_column("Force (ADX)", justify="center")
    table.add_column("Momentum (Delta)", justify="center", style="bold green")
    table.add_column("Funding (Foule)", justify="right", style="blue")

    for sym in TRADING_CONFIG['symbols']:
        st = states[sym]
        in_pos, px, prob_up, adx_val, sym_trend, drv = process_symbol(sym, news, btc_t)
        
        # Calcul des Metriques
        fund = drv.get('funding_rate', 0.0) * 100
        delta = drv.get('volume_delta', 0.0) * 100
        prob_txt = f"{prob_up*100:.0f}% / {(1-prob_up)*100:.0f}%"

        # Definition du Statut Humain
        l_pos = st['positions']['LONG']
        s_pos = st['positions']['SHORT']
        
        if l_pos['active'] or s_pos['active']:
            side = "LONG" if l_pos['active'] else "SHORT"
            pos = l_pos if l_pos['active'] else s_pos
            status_txt = f"[bold green]🚀 {side} EN COURS[/bold green]"
            if pos['be']: status_txt = f"[bold cyan]🛡️ SECURED (BE)[/bold cyan]"
            if pos['trailing']: status_txt = f"[bold magenta]💰 LOCKED (WIN)[/bold magenta]"
        elif time.time() < st['freeze_until']:
            status_txt = "[bold blue]❄️ QUARANTAINE[/bold blue]"
        elif st['reentry_count']['LONG'] > 0 or st['reentry_count']['SHORT'] > 0:
            status_txt = "[bold yellow]🔫 SNIPER RE-ENTRY[/bold yellow]"
        else:
            status_txt = "[dim]📡 SCANNING[/dim]"

        # Force (ADX) avec confirmation de tendance V6.3.3
        adx_label = f"[bold red]{adx_val:.1f} ({sym_trend})[/bold red]" if adx_val > 25 else f"[dim]{adx_val:.1f} (FAIBLE)[/dim]"

        table.add_row(
            sym,
            status_txt,
            f"{px:.4f}" if px > 0 else "-",
            prob_txt,
            adx_label,
            f"{delta:+.1f}%",
            f"{fund:.4f}%"
        )
        time.sleep(0.1)

    console.print(table)

if __name__ == "__main__":
    console.print(f"[on blue bold] 🛡️ V6.3.1 INSTITUTIONAL SYSTEM ACTIVATED [/on blue bold]")
    analyze_portfolio()
    schedule.every(1).minutes.do(analyze_portfolio)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        log_error("MAIN_LOOP", str(e), critical=True)
        console.print("[red]Arrêt V6.3.1.[/red]")
