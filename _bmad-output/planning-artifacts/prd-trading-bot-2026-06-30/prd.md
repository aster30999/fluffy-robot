---
title: "PRD - Solana Trading Bot"
status: draft
created: 2026-06-30
updated: 2026-06-30
author: asteroid
version: 1.0
type: internal-tool
stakes: launch
---

# Product Requirements Document - Solana Trading Bot

## 📌 Executive Summary

Création d'un **bot de trading automatique personnel** pour Solana qui :
- Récupère les prix en temps réel via **Jupiter API V2 HTTP**
- Analyse des indicateurs techniques (RSI, MACD, Volume, Support/Resistance, Ichimoku)
- Prend des décisions d'achat/vente automatiques (spot trading)
- Exécute les trades via Jupiter Order & Execute
- **Développement sur Devnet** avec un wallet pré-financé (5 SOL)
- **Production sur Mainnet** après validation et backtesting

**Objectif** : Automatiser le day trading personnel avec gestion des risques intégrée.

---

## 🎯 Vision & Objectives

### Vision
Créer un **bot de trading algorithmique personnel** sur Solana pour automatiser mes propres stratégies de day trading avec une gestion des risques rigoureuse.

### Objectifs Principaux
1. ✅ **Fonctionnel** : Bot opérationnel avec exécution réelle de trades
2. ✅ **Modulaire** : Architecture permettant d'ajouter/supprimer des indicateurs et stratégies
3. ✅ **Sécurisé** : Gestion des risques intégrée (stop-loss, take-profit, position sizing)
4. ✅ **Analysable** : Historique des trades et backtesting possible
5. ✅ **Multi-paires** : Prise en charge de plusieurs paires de trading simultanées
6. ✅ **Documenté** : Code et processus clairs pour maintenance personnelle

### Non-Objectifs (Out of Scope)
- ❌ Margin trading / leveraged trading
- ❌ Arbitrage entre DEX
- ❌ Market making
- ❌ Interface graphique (CLI uniquement pour v1)
- ❌ Open-source / démocratisation (projet personnel)

---

## 👥 Stakeholders

| Rôle | Nom | Responsabilités | Contact |
|------|-----|------------------|---------|
| Product Owner | asteroid | Vision, priorisation, validation | - |
| Développeur | Mistral Vibe | Implémentation technique | - |
| Utilisateur | Développeurs/Traders | Feedback, testing, contribution | - |

---

## 🎨 User Journeys

### UJ-1 : Configuration Initial du Bot
**Protagoniste** : Alice, utilisateur qui veut trader sur plusieurs paires simultanément

1. Alice clone le dépôt GitHub
2. Elle installe les dépendances (`pip install -r requirements.txt`)
3. Elle configure son `.env` avec :
   - `SOLANA_RPC_URL=https://api.devnet.solana.com` (Devnet pour le développement)
   - `JUPITER_API_URL=https://api.jup.ag/swap/v2`
   - `WALLET_PRIVATE_KEY=...` (ou utilisation du wallet par défaut)
4. Elle modifie `config/settings.py` pour :
   - **Sélectionner plusieurs paires de trading** (ex: SOL/USDC, SOL/USDT, ETH/SOL)
   - Configurer les seuils d'indicateurs par paire (RSI > 70 = vente, RSI < 30 = achat)
   - Définir les montants à trader par paire (ex: max 0.5 SOL par trade)
5. Elle lance le bot : `python main.py --pairs SOL/USDC,SOL/USDT,ETH/SOL --strategy mean_reversion --dry-run`

**Resultat** : Bot configuré pour trader sur N paires simultanément (mode dry-run pour test)

---

### UJ-2 : Exécution d'une Session de Trading
**Protagoniste** : Bob, trader qui veut automatiser ses signaux sur plusieurs paires

1. Bob lance le bot en mode réel : `python main.py --pairs SOL/USDC,SOL/USDT --strategy momentum`
2. Le bot, **pour chaque paire configurée** :
   - [T0] Récupère le prix actuel via Jupiter API
   - [T0] Calcule les indicateurs (RSI, MACD, etc.) sur les dernières données
   - [T0] Vérifie les conditions de trading
   - [T0] Si signal d'achat → exécute un buy order via Jupiter
   - [T+1min] Passe à la paire suivante (ou attende si toutes faites)
   - [T+5min] Répète l'analyse pour toutes les paires
3. Bob reçoit des logs en temps réel pour **toutes les paires** :
   ```
   [10:30:00] [SOL/USDC] Price: $150.25 | RSI: 28.5 | Signal: BUY
   [10:30:05] [SOL/USDC] Exécuting buy order: 0.1 SOL @ $150.25
   [10:30:10] [SOL/USDC] ✅ Transaction réussie: https://explorer.solana.com/tx/...?cluster=devnet
   [10:30:10] [SOL/USDT] Price: $150.30 | RSI: 65.2 | Signal: NEUTRAL
   [10:30:10] Portfolio: 4.9 SOL | 15.025 USDC | 10.0 USDT
   ```
4. Bob peut arrêter le bot à tout moment avec `Ctrl+C`

**Resultat** : Session de trading exécutée sur N paires simultanément avec transparence totale

---

### UJ-3 : Analyse Post-Trading
**Protagoniste** : Charlie, analyste qui veut optimiser sa stratégie

1. Charlie consulte le fichier `data/trades_history.json` généré automatiquement
2. Il lance le backtesting : `python backtest.py --strategy momentum --period 7d`
3. Le bot simule les trades sur les données historiques et génère :
   - Taux de réussite des signaux
   - Profit/Loss moyen par trade
   - Max drawdown
   - Sharpe ratio
4. Charlie ajuste ses paramètres dans `config/strategies/momentum.yaml`

**Resultat** : Stratégie optimisée basée sur des données concrètes

---

## ✨ Features & Functional Requirements

### 📊 Core Trading Engine

| ID | Feature | Description | Priority | Status |
|----|---------|-------------|----------|--------|
| FR-001 | Price Data Fetching | Récupérer les prix en temps réel via Jupiter API V2 | P0 | TODO |
| FR-002 | Token Balance Tracking | Suivre les balances SOL et tokens du wallet | P0 | TODO |
| FR-003 | Transaction Execution | Exécuter des swaps via Jupiter Order & Execute | P0 | TODO |
| FR-004 | Trade History Logging | Enregistrer tous les trades exécutés | P0 | TODO |

**FR-001 : Price Data Fetching**
- [ ] Récupérer le prix actuel d'une paire (ex: SOL/USDC)
- [ ] Supporter les endpoints Jupiter API V2 :
  - `/quote` pour obtenir un devis
  - `/swap` pour exécuter un trade (ou `/order` + `/execute`)
- [ ] Gérer les erreurs API (rate limiting, timeout, invalid pair)
- [ ] Cache des prix pendant X secondes pour éviter le spam API

**FR-002 : Token Balance Tracking**
- [ ] Récupérer le balance SOL du wallet
- [ ] Récupérer les balances de tous les tokens SPL
- [ ] Utiliser Solana RPC `getBalance` et `getTokenAccountsByOwner`
- [ ] Mettre à jour les balances après chaque trade

**FR-003 : Transaction Execution**
- [ ] Construire une transaction de swap via Jupiter API V2
- [ ] Signer la transaction avec la clé privée du wallet
- [ ] Envoyer la transaction via Jupiter `/execute` endpoint
- [ ] Vérifier la confirmation de la transaction
- [ ] Gérer les erreurs :
  - Insufficient funds
  - Slippage trop élevé
  - Timeout
  - Invalid signature

**FR-004 : Trade History Logging**
- [ ] Enregistrer chaque trade avec :
  - Timestamp
  - Type (BUY/SELL)
  - Token pair (ex: SOL/USDC)
  - Amount in
  - Amount out
  - Price
  - Transaction signature
  - Status (SUCCESS/FAILED)
  - Error message (si failed)
- [ ] Stocker dans un fichier JSON structuré
- [ ] Afficher un résumé à la fin de chaque session

---

### 📈 Technical Indicators

| ID | Feature | Description | Priority | Status |
|----|---------|-------------|----------|--------|
| FR-010 | Indicator Framework | Architecture modulaire pour ajouter des indicateurs | P0 | TODO |
| FR-011 | RSI (Relative Strength Index) | Indice de force relative (période configurable) | P0 | TODO |
| FR-012 | MACD (Moving Average Convergence Divergence) | Indicateur de tendance et momentum | P0 | TODO |
| FR-013 | Volume Analysis | Analyse du volume de trading | P1 | TODO |
| FR-014 | Support & Resistance Levels | Identification des niveaux clés | P1 | TODO |
| FR-015 | Ichimoku Cloud | Nuage d'Ichimoku (MMA/SMA) | P1 | TODO |

**FR-010 : Indicator Framework**
- [ ] Interface commune pour tous les indicateurs :
  ```python
  class BaseIndicator:
      def calculate(self, price_data: List[Candle]) -> float:
          pass
      def signal(self, value: float) -> Signal:
          pass
  ```
- [ ] Gestion des périodes/configurations par indicateur
- [ ] Cache des valeurs calculées pour performance

**FR-011 : RSI**
- [ ] Calcul du RSI sur N périodes (default: 14)
- [ ] Signaux :
  - RSI > 70 → Overbought → SELL
  - RSI < 30 → Oversold → BUY
- [ ] Configurable via fichier YAML

**FR-012 : MACD**
- [ ] Calcul de la ligne MACD, Signal et Histogramme
- [ ] Paramètres configurables : Fast EMA (12), Slow EMA (26), Signal (9)
- [ ] Signaux :
  - MACD > Signal → BUY
  - MACD < Signal → SELL
  - Crossover pour confirmation

**FR-013 : Volume Analysis**
- [ ] Calcul du volume moyen sur N périodes
- [ ] Détection des pics de volume (breakout possible)
- [ ] Confirmation des signaux avec le volume

**FR-014 : Support & Resistance**
- [ ] Identification automatique des niveaux de support/résistance
- [ ] Méthode : Pivot points, Fractals, ou High/Low des N dernières périodes
- [ ] Alertes quand le prix approche un niveau clé

**FR-015 : Ichimoku Cloud**
- [ ] Calcul des 5 lignes : Tenkan-sen, Kijun-sen, Senkou Span A/B, Chikou Span
- [ ] Détection des signaux :
  - Price > Cloud → Bullish
  - Price < Cloud → Bearish
  - Tenkan/Kijun crossover

---

### 🤖 Decision Engine

| ID | Feature | Description | Priority | Status |
|----|---------|-------------|----------|--------|
| FR-020 | Signal Aggregation | Agrégation des signaux de tous les indicateurs | P0 | TODO |
| FR-021 | Decision Rules | Règles de décision configurables | P0 | TODO |
| FR-022 | Strategy Framework | Framework pour implémenter des stratégies | P0 | TODO |
| FR-023 | Dry Run Mode | Mode simulation sans exécution réelle | P0 | TODO |

**FR-020 : Signal Aggregation**
- [ ] Chaque indicateur produit un signal : BUY, SELL, NEUTRAL
- [ ] Pondération des signaux (ex: RSI = 30%, MACD = 25%, etc.)
- [ ] Calcul d'un score global (0-100)
- [ ] Seuils configurables :
  - Score > 70 → BUY
  - Score < 30 → SELL
  - 30 ≤ Score ≤ 70 → NEUTRAL

**FR-021 : Decision Rules**
- [ ] Règles basées sur :
  - Combinaison d'indicateurs
  - Conditions de marché (volatilité, tendance)
  - Position actuelle (éviter les trades opposés)
- [ ] Exemple :
  ```yaml
  rules:
    buy:
      - rsi < 30
      - macd > signal
      - volume > average_volume * 1.5
    sell:
      - rsi > 70
      - macd < signal
  ```

**FR-022 : Strategy Framework**
- [ ] Interface pour les stratégies :
  ```python
  class BaseStrategy:
      def analyze(self, market_data: MarketData, portfolio: Portfolio) -> Decision:
          pass
      def configure(self, config: Dict):
          pass
  ```
- [ ] Stratégies incluses :
  - Mean Reversion
  - Momentum
  - Breakout
  - Trend Following

**FR-023 : Dry Run Mode**
- [ ] Mode `--dry-run` qui :
  - Calcule les signaux
  - Affiche ce qui aurait été tradé
  - N'exécute PAS les transactions
  - Enregistre dans un fichier séparé `dry_run_trades.json`

---

### 🛡️ Risk Management

| ID | Feature | Description | Priority | Status |
|----|---------|-------------|----------|--------|
| FR-030 | Position Sizing | Calcul de la taille de position | P0 | TODO |
| FR-031 | Stop Loss | Ordre stop-loss automatique | P0 | TODO |
| FR-032 | Take Profit | Prise de profit automatique | P0 | TODO |
| FR-033 | Max Drawdown Protection | Limite de perte maximale | P1 | TODO |
| FR-034 | Trade Frequency Limit | Limite le nombre de trades par période | P1 | TODO |

**FR-030 : Position Sizing**
- [ ] Calcul du montant à trader basé sur :
  - Pourcentage du portefeuille (ex: max 10% par trade)
  - Montant fixe configurable
  - Risque par trade (ex: max 1% du portefeuille en risque)
- [ ] Exemple : Portfolio = 5 SOL, Risk per trade = 1% → Max loss = 0.05 SOL

**FR-031 : Stop Loss**
- [ ] Stop-loss basé sur :
  - Pourcentage (ex: -5%)
  - Prix absolu
  - Trailing stop
- [ ] Exécution automatique via Jupiter ou surveillance continue

**FR-032 : Take Profit**
- [ ] Take-profit basé sur :
  - Pourcentage (ex: +10%)
  - Prix absolu
  - Ratio Risk/Reward (ex: 1:2)

**FR-033 : Max Drawdown Protection**
- [ ] Limite globale : si drawdown > X%, arrêter le bot
- [ ] Reset automatique après Y heures

**FR-034 : Trade Frequency Limit**
- [ ] Max Z trades par heure/jour
- [ ] Cooldown période entre les trades (ex: 5 minutes)

---

### 📊 Monitoring & Analytics

| ID | Feature | Description | Priority | Status |
|----|---------|-------------|----------|--------|
| FR-040 | Real-time Logging | Logs détaillés en temps réel | P1 | TODO |
| FR-041 | Performance Metrics | Métriques de performance | P1 | TODO |
| FR-042 | Session Summary | Résumé de session | P1 | TODO |
| FR-043 | Alerts & Notifications | Alertes pour événements importants | P2 | TODO |

**FR-040 : Real-time Logging**
- [ ] Logs structurés avec niveaux : DEBUG, INFO, WARNING, ERROR
- [ ] Format :
  ```
  [TIMESTAMP] [LEVEL] [COMPONENT] message
  [10:30:00] [INFO] [PRICE_FETCHER] SOL/USDC: $150.25
  [10:30:05] [INFO] [DECISION_ENGINE] Signal: BUY (Score: 85/100)
  [10:30:10] [SUCCESS] [TRADE_EXECUTOR] Buy 0.1 SOL @ $150.25
  ```

**FR-041 : Performance Metrics**
- [ ] Métriques calculées :
  - PnL (Profit and Loss)
  - Win rate (% de trades gagnants)
  - Average profit/loss
  - Max drawdown
  - Sharpe ratio
  - Sortino ratio

**FR-042 : Session Summary**
- [ ] À la fin de chaque session, générer :
  - Nombre de trades exécutés
  - PnL total
  - Meilleur/worst trade
  - Temps d'exécution moyen par trade

**FR-043 : Alerts & Notifications**
- [ ] Alertes pour :
  - Nouveau trade exécuté
  - Stop-loss/take-profit déclenché
  - Erreur critique
  - Drawdown > seuil
- [ ] Canaux : Console, fichier, optionnel Telegram/Discord (futur)

---

### 🧪 Backtesting

| ID | Feature | Description | Priority | Status |
|----|---------|-------------|----------|--------|
| FR-050 | Historical Data Fetching | Récupération de données historiques | P1 | TODO |
| FR-051 | Backtest Engine | Moteur de backtesting | P1 | TODO |
| FR-052 | Performance Report | Rapport de performance | P1 | TODO |

**FR-050 : Historical Data Fetching**
- [ ] Récupérer des données OHLCV (Open, High, Low, Close, Volume)
- [ ] Sources possibles :
  - Jupiter API (si disponible)
  - Solana RPC (getSignaturesForAddress pour les swaps)
  - Birdeye API (si clé disponible)
  - Fichiers CSV locaux
- [ ] Période configurable (1h, 1d, 7d, 30d)

**FR-051 : Backtest Engine**
- [ ] Simuler l'exécution des trades sur données historiques
- [ ] Prendre en compte :
  - Slippage
  - Frais de transaction
  - Latence
- [ ] Comparer avec un hold simple (benchmark)

**FR-052 : Performance Report**
- [ ] Générer un rapport Markdown/HTML avec :
  - Courbe de equity
  - Distribution des trades
  - Métriques détaillées
  - Visualisations (optionnel avec matplotlib)

---

### ⚙️ Configuration & CLI

| ID | Feature | Description | Priority | Status |
|----|---------|-------------|----------|--------|
| FR-060 | Configuration Files | Fichiers de configuration YAML/JSON | P0 | TODO |
| FR-061 | CLI Interface | Interface en ligne de commande | P0 | TODO |
| FR-062 | Environment Variables | Variables d'environnement pour les clés sensibles | P0 | TODO |

**FR-060 : Configuration Files**
- [ ] Structure :
  ```
  config/
  ├── settings.py          # Paramètres globaux
  ├── tokens.yaml         # Liste des tokens/paires à trader
  ├── strategies/         # Configuration par stratégie
  │   ├── mean_reversion.yaml
  │   └── momentum.yaml
  └── indicators.yaml      # Configuration des indicateurs
  ```

**FR-061 : CLI Interface**
- [ ] Commandes principales :
  ```bash
  # Lancer le bot
  python main.py --strategy momentum --pair SOL/USDC
  
  # Mode dry-run
  python main.py --strategy momentum --dry-run
  
  # Backtesting
  python backtest.py --strategy momentum --period 7d
  
  # Voir l'aide
  python main.py --help
  ```
- [ ] Options :
  - `--strategy` : Stratégie à utiliser
  - `--pair` : Paire de trading
  - `--amount` : Montant par trade
  - `--dry-run` : Mode simulation
  - `--verbose` : Logs détaillés
  - `--config` : Fichier de configuration custom

**FR-062 : Environment Variables**
- [ ] Variables requises :
  ```
  SOLANA_RPC_URL=https://api.devnet.solana.com
  JUPITER_API_URL=https://api.jup.ag/swap/v2
  WALLET_PRIVATE_KEY=...  # Optionnel (sinon wallet par défaut)
  JUPITER_API_KEY=...     # Optionnel (pour rate limit plus élevé)
  ```

---

## 🚀 Non-Functional Requirements

### Performance
| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-001 | Latence de récupération des prix | < 2s | P0 |
| NFR-002 | Latence d'exécution d'un trade | < 10s | P0 |
| NFR-003 | Fréquence d'analyse | Toutes les 1-5 minutes | P0 |
| NFR-004 | Mémoire utilisée | < 100MB | P1 |
| NFR-005 | CPU utilisée | < 10% | P1 |

### Reliability
| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-010 | Uptime | > 99% pendant une session | P0 |
| NFR-011 | Retry sur échec API | 3 tentatives avec backoff exponentiel | P0 |
| NFR-012 | Récupération après crash | Redémarrage propre | P1 |

### Security
| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| NFR-020 | Clé privée sécurisée | Never logged, never exposed | P0 |
| NFR-021 | Validation des transactions | Vérifier les montants avant signature | P0 |
| NFR-022 | Limite des pertes | Max loss configurable (ex: 10% du portefeuille) | P0 |

### Maintainability
| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| NFR-030 | Code documenté | Docstrings pour toutes les fonctions publiques | P0 |
| NFR-031 | Tests unitaires | Couverture > 80% | P1 |
| NFR-032 | Logging structuré | Format JSON pour analyse | P1 |
| NFR-033 | Modularité | Chaque composant peut être remplacé | P0 |

### Usability
| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| NFR-040 | Messages clairs | Logs compréhensibles pour non-développeurs | P0 |
| NFR-041 | Documentation | README complet avec exemples | P0 |
| NFR-042 | Configuration simple | Fichiers YAML/JSON auto-explicatifs | P1 |

---

## 📦 Technical Constraints

| ID | Contrainte | Description |
|----|------------|-------------|
| TC-001 | Devnet pour développement | Développement et tests sur Devnet uniquement |
| TC-002 | Mainnet pour production | Bascule sur Mainnet après validation et backtesting |
| TC-003 | Wallet existant | Utilisation du wallet avec 5 SOL déjà claimés (Devnet) |
| TC-004 | Jupiter API V2 | Utilisation exclusive de Jupiter API V2 HTTP |
| TC-005 | Python 3.10+ | Compatibilité ascendante |
| TC-006 | Async/Promises | Code asynchrone pour performance |
| TC-007 | Pas de GUI | CLI uniquement pour v1 |
| TC-008 | Multi-paires | Support de N paires de trading simultanées |

---

## ⚠️ Assumptions

| ID | Assumption | Validation Plan | Owner |
|----|------------|-----------------|-------|
| A-001 | Jupiter API V2 supporte SOL/USDC sur Devnet | Tester avec une requête simple | asteroid |
| A-002 | Le wallet a assez de SOL pour les frais de transaction | Vérifier balance avant chaque trade | Bot |
| A-003 | Les indicateurs peuvent être calculés avec les données Jupiter | Vérifier le format des données retournées | Développeur |
| A-004 | Pas de rate limiting bloquant avec Jupiter API publique | Monitorer les erreurs 429 | Bot |

---

## 🔍 Open Questions

| ID | Question | Priority | Status |
|----|---------|----------|--------|
| OQ-001 | Jupiter API V2 a-t-il un endpoint pour l'historique des prix ? | P0 | **À valider** |
| OQ-002 | Quels tokens sont supportés sur Devnet par Jupiter ? | P0 | **À valider** |
| OQ-003 | Comment gérer le slippage de manière optimale ? | P1 | À étudier |
| OQ-004 | Faut-il supporter d'autres DEX que Jupiter ? | P2 | À discuter |

---

## 📊 Success Metrics

| Métrique | Cible | Période | Méthode de mesure |
|----------|-------|---------|-------------------|
| Taux de réussite des trades | > 60% | Par session | (Trades gagnants / Total trades) × 100 |
| Profit moyen par trade | > 0.5% | Par session | (Profit total / Nombre de trades) |
| Drawdown maximum | < 10% | Par session | (Perte max depuis le sommet) |
| Temps moyen par trade | < 15s | Par trade | De signal à exécution |
| Sharpe Ratio | > 1.5 | Par session | (Retour moyen - Retour sans risque) / Volatilité |

---

## 🎯 MVP Scope (V1)

### Inclus dans V1
- ✅ Price Fetcher (Jupiter API V2)
- ✅ Trade Executor (Jupiter Order & Execute)
- ✅ Balance Tracker (SOL + 1 token)
- ✅ Indicateurs : RSI, MACD
- ✅ Decision Engine basique (règles simples)
- ✅ 1 stratégie : Mean Reversion
- ✅ Risk Management : Position Sizing, Stop Loss basique
- ✅ Logging en temps réel
- ✅ Mode Dry Run
- ✅ CLI basique

### Exclus de V1 (Futur)
- ❌ Ichimoku, Support/Resistance, Volume Analysis
- ❌ Backtesting complet
- ❌ Alertes Telegram/Discord
- ❌ Multiple strategies
- ❌ Dashboard web
- ❌ Trading sur Mainnet

---

## 📅 Timeline & Milestones

| Milestone | Date Cible | Livrables |
|-----------|------------|-----------|
| M1 : PRD & Architecture | 2026-06-30 | PRD finalisé, Architecture validée |
| M2 : Core Engine | 2026-07-02 | Price Fetcher, Trade Executor, Balance Tracker |
| M3 : Indicators & Decision | 2026-07-04 | RSI, MACD, Decision Engine |
| M4 : Strategy & Risk Mgmt | 2026-07-06 | Mean Reversion, Stop Loss, Position Sizing |
| M5 : Testing & Validation | 2026-07-08 | Tests unitaires, Dry Run sur Devnet |
| M6 : First Real Trade | 2026-07-10 | Premier trade réel exécuté |
| M7 : Monitoring & Analytics | 2026-07-12 | Métriques, Logging amélioré |
| M8 : V1 Release | 2026-07-14 | Version stable avec documentation |

---

## 🔗 Dependencies

### External Dependencies
| Dépendance | Version | Usage |
|------------|---------|-------|
| Python | 3.10+ | Language principal |
| solana-py | 0.36.6+ | Interaction avec Solana |
| solders | 0.27.0+ | Structures de données Solana |
| httpx | 0.28.1+ | Requêtes HTTP async |
| pydantic | 2.0+ | Validation des données |
| pyyaml | 6.0+ | Configuration YAML |
| python-dotenv | 1.0+ | Variables d'environnement |

### Internal Dependencies
- Module `core/price_fetcher.py` dépend de : rien (indépendant)
- Module `core/indicators/` dépend de : `price_fetcher`
- Module `core/decision_engine.py` dépend de : `indicators`, `price_fetcher`
- Module `core/trade_executor.py` dépend de : `decision_engine`, `price_fetcher`

---

## 🚨 Risks & Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| R-001 : Jupiter API rate limiting | Moyenne | Élevé | Utiliser API key, implémenter retry avec backoff |
| R-002 : Bug dans le signing des transactions | Faible | Critique | Tests unitaires exhaustifs, vérification manuelle des premiers trades |
| R-003 : Slippage trop élevé | Moyenne | Élevé | Limiter les montants, vérifier le slippage avant exécution |
| R-004 : Changement dans Jupiter API | Faible | Élevé | Monitorer les changelogs, tests d'intégration réguliers |
| R-005 : Perte de fonds due à un bug | Très Faible | Catastrophique | Dry run obligatoire avant mode réel, limites strictes |
| R-006 : Indicateurs mal calculés | Moyenne | Moyen | Backtesting contre données connues, validation manuelle |

---

## 📝 Notes & References

### Documentation Externe
- [Jupiter API V2 Documentation](https://dev.jup.ag/swap/order-and-execute)
- [Solana Python SDK](https://github.com/michaelhly/solana-py)
- [Solders Documentation](https://github.com/gemworks/solders)

### Décisions Techniques
- **Jupiter API V2 HTTP** : Choix basé sur la stabilité et la maintenance officielle (DevRel)
- **Mix Libs + HTTP pour Solana** : Libs (`solana-py`, `solders`) pour ce qui est complexe (signing, transactions), HTTP direct pour les queries simples (balances)
- **Devnet uniquement** : Pas de risque de perte de fonds réels pendant le développement

### Glossaire
- **Devnet** : Réseau de test Solana (SOL sans valeur réelle)
- **Jupiter** : Aggregator de liquidité sur Solana
- **RSI** : Relative Strength Index (indicateur de momentum)
- **MACD** : Moving Average Convergence Divergence (indicateur de tendance)
- **Dry Run** : Mode simulation sans exécution réelle de trades
- **Drawdown** : Pourcentage de perte par rapport au sommet du portefeuille

---

## 🏁 Next Steps

1. **Valider le PRD** avec le product owner (asteroid)
2. **Créer l'architecture technique** avec `bmad-architecture`
3. **Découper en épics et user stories** avec `bmad-create-epics-and-stories`
4. **Planifier le sprint** avec `bmad-sprint-planning`
5. **Commencer l'implémentation** avec `bmad-dev-story`

---

*Document généré par Mistral Vibe - Co-Authored-By: Mistral Vibe <vibe@mistral.ai>*