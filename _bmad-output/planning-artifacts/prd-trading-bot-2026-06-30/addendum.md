# Addendum - Solana Trading Bot PRD

*Ce document contient les détails techniques, alternatives rejetées, et informations complémentaires qui ne trouvent pas leur place dans le PRD principal.*

---

## 🔧 Technical Decisions

### Pourquoi Jupiter API V2 HTTP ?

**Alternatives considérées :**

| Solution | Type | Avantages | Inconvénients | Decision |
|----------|------|-----------|---------------|----------|
| Jupiter API V2 HTTP | API REST | ✅ Stable, maintenu par DevRel, meilleur pricing, contrôle total | ⚠️ Gestion manuelle des transactions | **✅ Sélectionné** |
| jup-python-sdk | SDK Python | ✅ Plus simple, abstrait la complexité | ⚠️ Problèmes avec Ultra API (cf. README existant), moins de contrôle | ❌ Rejeté |
| jupiter-python-sdk | SDK Python | - | ❌ Déprécié | ❌ Rejeté |
| Birdeye API | API REST | ✅ Données riches, historique disponible | ⚠️ Coût, pas spécialisé pour swaps | ❌ Rejeté pour V1 |
| Raydium API | API REST | ✅ Direct DEX access | ⚠️ Moins de liquidité, plus complexe | ❌ Rejeté pour V1 |

**Justification :**
Le README existant dans ton projet montre clairement que Jupiter API V2 HTTP est la solution la plus stable et la mieux maintenue. Les SDKs ont des problèmes documentés (Ultra API issues), et une approche directe via HTTP nous donne un contrôle total sur le processus de swap, ce qui est crucial pour un bot de trading où chaque détail compte.

---

### Pourquoi un Mix Libs + HTTP pour Solana ?

**Décision :** Utiliser `solana-py` et `solders` pour ce qui est complexe, et HTTP direct pour les requêtes simples.

**Rationale :**

1. **Pourquoi utiliser les libs (`solana-py`, `solders`) ?**
   - Gestion des keypairs : `Keypair.from_bytes()`, signing
   - Serialization/déserialization des transactions : `VersionedTransaction.deserialize()`
   - Structures de données bien testées : `Pubkey`, `Transaction`, etc.
   - Moins de code à écrire, moins de bugs potentiels

2. **Pourquoi utiliser HTTP direct ?**
   - Requêtes simples comme `getBalance` ou `getTokenAccountsByOwner` sont plus légères sans les libs
   - Moins de dépendances (les libs ont elles-mêmes des dépendances)
   - Plus facile à déboguer (on voit exactement ce qui est envoyé/reçu)
   - Plus flexible (on peut facilement ajouter des paramètres custom)

**Exemples concrets :**
```python
# Avec libs (pour les transactions)
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
import base64

client = AsyncClient(rpc_url)
wallet = Keypair.from_bytes(secret_key)
# Pour signer une transaction Jupiter
tx_bytes = base64.b64decode(jupiter_tx_base64)
tx = VersionedTransaction.deserialize(tx_bytes)
tx.sign([wallet])
signed_tx = base64.b64encode(tx.serialize()).decode('utf-8')

# Avec HTTP direct (pour les balances)
import httpx
async with httpx.AsyncClient() as http_client:
    response = await http_client.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_pubkey]
        }
    )
    balance = response.json()["result"]
```

---

## 🗺️ Architecture Overview (Preview)

*Cette section sera développée dans le document d'architecture, mais voici un aperçu pour contexte.*

```
┌─────────────────────────────────────────────────────────────────┐
│                        Solana Trading Bot                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │  Price Fetcher   │    │  Balance Tracker  │    │  Trade       │ │
│  │  (Jupiter API)   │───▶│  (Solana RPC)     │───▶│  Executor   │ │
│  └─────────────────┘    └─────────────────┘    │  (Jupiter)   │ │
│          │                         │                └──────┬──────┘ │
│          ▼                         ▼                       │        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Indicator Framework                      │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────┐  ┌─────────┐  │   │
│  │  │   RSI   │  │   MACD  │  │   Volume    │  │ Ichimoku │  │   │
│  │  └─────────┘  └─────────┘  └─────────────┘  └─────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Decision Engine                         │   │
│  │  - Signal Aggregation                                    │   │
│  │  - Strategy Application                                   │   │
│  │  - Risk Management Checks                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Main Loop                            │   │
│  │  1. Fetch prices                                          │   │
│  │  2. Fetch balances                                        │   │
│  │  3. Calculate indicators                                  │   │
│  │  4. Make decision                                         │   │
│  │  5. Execute trade (or log dry-run)                        │   │
│  │  6. Update state                                          │   │
│  │  7. Sleep (1-5 min)                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│         Data Storage          │
│  - trades_history.json        │
│  - dry_run_trades.json        │
│  - logs/                      │
│    - trading_YYYYMMDD.log     │
│    - errors_YYYYMMDD.log      │
└─────────────────────────────┘
```

---

## 📊 Data Flow

### Main Trading Loop

```mermaid
graph TD
    A[Start] --> B[Load Configuration]
    B --> C[Initialize Jupiter Client]
    C --> D[Initialize Solana Client]
    D --> E[Load Wallet]
    E --> F[Main Loop]
    
    F --> G[Fetch Prices]
    G --> H[Fetch Balances]
    H --> I[Calculate Indicators]
    I --> J[Apply Strategy Rules]
    J --> K{Trade Signal?}
    
    K -->|Yes| L[Calculate Position Size]
    L --> M[Check Risk Limits]
    M --> N{Passes Checks?}
    N -->|Yes| O[Execute Trade]
    N -->|No| P[Log: Risk check failed]
    O --> Q[Log Trade]
    
    K -->|No| R[Log: No signal]
    
    Q --> S[Update Portfolio]
    R --> S
    P --> S
    
    S --> T[Sleep 1-5 min]
    T --> F
    
    F -->. [Ctrl+C] --> U[Shutdown]
    U --> V[Save State]
    V --> W[End]
```

---

## 🎯 Strategy Implementation Details

### Mean Reversion Strategy

**Principe :** Acheter quand le prix est bas par rapport à sa moyenne, vendre quand il est haut.

**Indicateurs utilisés :**
- RSI (pour détecter sur-achat/survente)
- Bollinger Bands (optionnel, pour V2)

**Règles :**
```yaml
mean_reversion:
  rsi:
    buy_threshold: 30
    sell_threshold: 70
    period: 14
  
  bollinger:  # Optionnel pour V2
    period: 20
    std_dev: 2
    buy_threshold: -1  # Prix sous la bande inférieure
    sell_threshold: 1  # Prix au-dessus de la bande supérieure
  
  position_sizing:
    max_portfolio_risk: 0.01  # 1%
    max_trade_amount: 0.5    # SOL
  
  stop_loss:
    enabled: true
    percentage: 0.05  # 5%
  
  take_profit:
    enabled: true
    percentage: 0.10  # 10%
```

**Logique :**
```python
if rsi < buy_threshold:
    signal = BUY
    amount = calculate_position_size(risk=0.01)
elif rsi > sell_threshold:
    signal = SELL
    amount = calculate_position_size(risk=0.01)
else:
    signal = NEUTRAL
```

---

### Momentum Strategy

**Principe :** Acheter quand le prix monte, vendre quand il descend (suivre la tendance).

**Indicateurs utilisés :**
- MACD (pour détecter la tendance et les changements)
- Moving Averages (pour confirmation)

**Règles :**
```yaml
momentum:
  macd:
    fast_ema: 12
    slow_ema: 26
    signal: 9
    buy_signal: macd > signal  # MACD au-dessus de sa ligne de signal
    sell_signal: macd < signal # MACD en-dessous de sa ligne de signal
  
  moving_averages:
    short: 10
    long: 50
    buy_confirmation: price > short_ma and short_ma > long_ma  # Trend up
    sell_confirmation: price < short_ma and short_ma < long_ma # Trend down
  
  position_sizing:
    max_portfolio_risk: 0.02  # 2%
    max_trade_amount: 1.0    # SOL
```

---

## 🔍 Open Questions Details

### OQ-001 : Jupiter API V2 a-t-il un endpoint pour l'historique des prix ?

**Contexte :** Pour le backtesting, nous avons besoin de données historiques (OHLCV).

**Recherche initiale :**
- Jupiter API V2 a principalement `/quote` et `/swap` pour les swaps en temps réel
- Pas d'endpoint historique documenté dans la [doc officielle](https://dev.jup.ag/swap/order-and-execute)

**Solutions possibles :**
1. Utiliser Solana RPC pour récupérer l'historique des transactions de swap
   - `getSignaturesForAddress` sur les pools Jupiter
   - Complexe à parser
2. Utiliser Birdeye API (nécessite une clé)
   - A des endpoints historiques
   - Coût potentiel
3. Utiliser des données locales (CSV) pour le backtesting initial
   - Simple mais moins flexible
4. Attendre une future version de Jupiter API

**Recommandation :** Commencer avec des données locales pour V1, puis intégrer Birdeye si clé disponible.

---

### OQ-002 : Quels tokens sont supportés sur Devnet par Jupiter ?

**Contexte :** Nous devons savoir quelles paires nous pouvons trader sur Devnet.

**À tester :**
1. SOL → USDC (le plus probable)
2. SOL → USDT
3. Autres paires populaires

**Méthode de test :**
```python
import httpx

JUPITER_API = "https://api.jup.ag/swap/v2"

async def test_pair(input_mint, output_mint):
    try:
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": "1000000000",  # 1 SOL en lamports
            "slippageBps": 100
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{JUPITER_API}/quote", params=params)
            return response.status_code == 200
    except Exception as e:
        return False

# Tester sur Devnet
SOL = "So11111111111111111111111111111111111111112"
USDC_DEVNET = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
USDT_DEVNET = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
```

**Attendu :** au moins SOL/USDC devrait fonctionner.

---

## 🛠️ Implementation Considerations

### Error Handling Strategy

**Principe :** Ne jamais crasher, toujours logging clair, retry intelligent.

```python
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0  # secondes
    max_delay: float = 30.0
    exponential_base: float = 2.0
    
    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        return min(delay, self.max_delay)

def retry_with_backoff(func, *args, **kwargs):
    config = RetryConfig()
    for attempt in range(config.max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == config.max_attempts - 1:
                raise
            delay = config.get_delay(attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
```

---

### Rate Limiting Management

**Jupiter API Rate Limits (public):**
- Sans clé API : ~10 requêtes/minute
- Avec clé API : ~100 requêtes/minute

**Stratégie :**
1. Utiliser une clé API si disponible (gratuit sur [Jupiter Portal](https://developers.jup.ag/portal))
2. Implémenter un cache pour les prix (TTL: 5-10 secondes)
3. Limiter la fréquence d'analyse (toutes les 1-5 minutes)
4. Utiliser `asyncio.Semaphore` pour limiter les requêtes concurrentes

```python
class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def wait(self):
        async with self.lock:
            now = time.time()
            # Supprimer les appels anciens
            self.calls = [t for t in self.calls if now - t < self.period]
            
            if len(self.calls) >= self.max_calls:
                oldest = self.calls[0]
                wait_time = self.period - (now - oldest)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Recalculer après le sleep
                    now = time.time()
                    self.calls = [t for t in self.calls if now - t < self.period]
            
            self.calls.append(now)
```

---

## 📚 Resources & References

### Jupiter API Documentation
- [Jupiter API V2 - Order & Execute](https://dev.jup.ag/swap/order-and-execute)
- [Jupiter API Reference](https://api.jup.ag/docs)
- [Jupiter Developers Portal](https://developers.jup.ag/portal)

### Solana Documentation
- [Solana RPC API](https://solana.com/docs/rpc)
- [Solana Python SDK](https://github.com/michaelhly/solana-py)
- [Solders Documentation](https://github.com/gemworks/solders)

### Trading Indicators References
- [RSI - Investopedia](https://www.investopedia.com/terms/r/rsi.asp)
- [MACD - Investopedia](https://www.investopedia.com/terms/m/macd.asp)
- [Ichimoku Cloud - Investopedia](https://www.investopedia.com/terms/i/ichimoku-cloud.asp)

---

*Document complémentaire au PRD - Co-Authored-By: Mistral Vibe <vibe@mistral.ai>*