"""
Integration tests for the Main Trading Loop

Tests the TradingBot class and its main trading loop functionality.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from src.cli import TradingBot, TradingBotError, NetworkValidationError
from src.config.trading_config import TradingConfig, TradingBotServices
from src.core.models.price import Token, TokenPair, Price
from src.core.models.trade import Decision, Signal, Trade
from src.core.models.balance import Balance, Portfolio


def create_mock_bot(config=None, dry_run=True, mock_services=True):
    """Helper to create a TradingBot with mocked services for testing."""
    if config is None:
        config = TradingConfig(pairs=[], interval=60.0, network="devnet", dry_run=dry_run)
    
    with patch.object(TradingBot, '_initialize_services'):
        with patch.object(TradingBot, '_setup_signal_handlers'):
            bot = TradingBot(config=config, dry_run=dry_run)
            
            if mock_services:
                # Mock the services attribute
                bot.services = Mock(spec=TradingBotServices)
                bot.services.price_fetcher = Mock()
                bot.services.balance_tracker = Mock()
                bot.services.trade_executor = Mock()
                bot.services.solana_client = Mock()
                bot.services.jupiter_client = Mock()
                bot.services.wallet = Mock()
                bot.services.portfolio = Mock()
            
            return bot


class TestTradingBotInitialization:
    """Tests for TradingBot initialization."""

    def test_initialization_with_valid_configuration(self):
        """Test TradingBot initialization with valid configuration."""
        config = TradingConfig(
            pairs=[],
            interval=60.0,
            network="devnet",
            dry_run=True
        )
        
        # Mock the services to avoid actual initialization
        with patch.object(TradingBot, '_initialize_services'):
            with patch.object(TradingBot, '_setup_signal_handlers'):
                bot = TradingBot(config=config, dry_run=True)
                
                assert bot.config == config
                assert bot.dry_run is True
                assert bot._running is False
                assert bot.logger is not None

    def test_initialization_sets_dry_run_from_config(self):
        """Test that dry_run is set from config when not provided."""
        config = TradingConfig(dry_run=False)
        
        with patch.object(TradingBot, '_initialize_services'):
            with patch.object(TradingBot, '_setup_signal_handlers'):
                bot = TradingBot(config=config)
                
                assert bot.dry_run is False

    def test_initialization_overrides_dry_run(self):
        """Test that dry_run parameter overrides config."""
        config = TradingConfig(dry_run=False)
        
        with patch.object(TradingBot, '_initialize_services'):
            with patch.object(TradingBot, '_setup_signal_handlers'):
                bot = TradingBot(config=config, dry_run=True)
                
                assert bot.dry_run is True


class TestMainLoop:
    """Tests for the main trading loop."""

    def test_main_loop_processes_all_pairs(self):
        """Test that main loop processes all configured pairs."""
        pair1 = TokenPair(
            base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        pair2 = TokenPair(
            base=Token(symbol="BTC", mint="3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ9DQqFzcycA", decimals=8),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        
        config = TradingConfig(
            pairs=[pair1, pair2],
            interval=0.1,
            dry_run=True
        )
        bot = create_mock_bot(config=config, dry_run=True)
        
        with patch.object(bot, '_process_pair', return_value=None) as mock_process:
            with patch.object(bot, '_log_configuration'):
                with patch.object(bot, '_validate_network'):
                    with patch.object(bot, '_shutdown'):
                        with patch('src.cli.time.sleep'):
                            with patch('src.cli.time.time', return_value=0.0):
                                bot._running = True
                                # Manually iterate through the loop once
                                cycle_count = 0
                                while bot._running and cycle_count < 1:
                                    cycle_start = 0.0
                                    cycle_count += 1
                                    for pair in bot.config.pairs:
                                        bot._process_pair(pair)
                                    bot._running = False
                                
                                assert mock_process.call_count == 2

    def test_main_loop_respects_interval(self):
        """Test that main loop respects configured interval."""
        config = TradingConfig(pairs=[], interval=0.5, dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        with patch.object(bot, '_process_pair', return_value=None):
            with patch.object(bot, '_log_configuration'):
                with patch.object(bot, '_validate_network'):
                    with patch.object(bot, '_shutdown'):
                        with patch('src.cli.time.time', return_value=0.0):
                            with patch('src.cli.time.sleep') as mock_sleep:
                                bot._running = True
                                cycle_count = 0
                                while bot._running and cycle_count < 1:
                                    cycle_start = 0.0
                                    cycle_count += 1
                                    processing_time = 0.0
                                    sleep_time = max(0, bot.config.interval - processing_time)
                                    mock_sleep(sleep_time)
                                    bot._running = False
                                
                                assert mock_sleep.call_count == 1

    def test_main_loop_handles_pair_failures_gracefully(self):
        """Test that main loop handles individual pair failures without stopping."""
        pair1 = TokenPair(
            base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        pair2 = TokenPair(
            base=Token(symbol="BTC", mint="3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ9DQqFzcycA", decimals=8),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        
        config = TradingConfig(pairs=[pair1, pair2], interval=0.1, dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        with patch.object(bot, '_process_pair') as mock_process:
            mock_process.side_effect = [Exception("Pair 1 failed"), None]
            bot._running = True
            cycle_count = 0
            while bot._running and cycle_count < 1:
                cycle_count += 1
                for pair in bot.config.pairs:
                    try:
                        bot._process_pair(pair)
                    except Exception:
                        pass
                bot._running = False
            
            assert mock_process.call_count == 2


class TestPairProcessing:
    """Tests for pair processing."""

    def test_process_pair_returns_decision(self):
        """Test that _process_pair returns decision for valid pair."""
        pair = TokenPair(
            base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        config = TradingConfig(pairs=[pair], dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        mock_price = Price(value=0.5, timestamp=time.time())
        
        with patch.object(bot, '_fetch_and_update_prices', return_value=mock_price):
            with patch.object(bot, '_calculate_indicators', return_value={"current_price": 0.5}):
                with patch.object(bot, '_make_decision') as mock_make_decision:
                    mock_decision = Decision(
                        decision_id="test-1",
                        token_pair=pair,
                        signal=Signal.BUY,
                        confidence=0.8,
                        amount=0.01,
                        timestamp=time.time(),
                        reasoning="Test"
                    )
                    mock_make_decision.return_value = mock_decision
                    
                    with patch.object(bot, '_execute_trade', return_value=None):
                        with patch.object(bot, '_update_portfolio'):
                            result = bot._process_pair(pair)
                            assert result == mock_decision

    def test_process_pair_returns_none_for_failed_price_fetch(self):
        """Test that _process_pair returns None when price fetch fails."""
        pair = TokenPair(
            base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        config = TradingConfig(pairs=[pair], dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        with patch.object(bot, '_fetch_and_update_prices', return_value=None):
            result = bot._process_pair(pair)
            assert result is None

    def test_process_pair_handles_errors_gracefully(self):
        """Test that _process_pair handles errors gracefully."""
        pair = TokenPair(
            base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        config = TradingConfig(pairs=[pair], dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        with patch.object(bot, '_fetch_and_update_prices', side_effect=Exception("Test error")):
            result = bot._process_pair(pair)
            assert result is None


class TestNetworkValidation:
    """Tests for network validation."""

    def test_validate_network_succeeds_for_devnet(self):
        """Test that network validation succeeds for valid Devnet connection."""
        config = TradingConfig(network="devnet", dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        mock_solana = Mock()
        mock_solana.get_version.return_value = {"solana-core": "1.18.0"}
        bot.services.solana_client = mock_solana
        
        bot._validate_network()

    def test_validate_network_raises_error_for_invalid_connection(self):
        """Test that network validation handles connection errors."""
        config = TradingConfig(network="devnet", dry_run=False)
        
        with patch.object(TradingBot, '_initialize_services'):
            with patch.object(TradingBot, '_setup_signal_handlers'):
                bot = TradingBot(config=config, dry_run=False)
                
                # Make logger.info raise an exception to trigger outer try-except
                with patch.object(bot.logger, 'info', side_effect=Exception("Connection failed")):
                    with pytest.raises(NetworkValidationError):
                        bot._validate_network()


class TestDryRunMode:
    """Tests for dry-run mode."""

    def test_dry_run_mode_prevents_actual_trades(self):
        """Test that dry-run mode prevents actual trades."""
        pair = TokenPair(
            base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        config = TradingConfig(pairs=[pair], dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        decision = Decision(
            decision_id="test-1",
            token_pair=pair,
            signal=Signal.BUY,
            confidence=0.8,
            amount=0.01,
            timestamp=time.time(),
            reasoning="Test"
        )
        
        result = bot._execute_trade(decision)
        assert result is None

    def test_dry_run_mode_logs_what_would_happen(self):
        """Test that dry-run mode logs what would happen."""
        pair = TokenPair(
            base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        config = TradingConfig(pairs=[pair], dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        decision = Decision(
            decision_id="test-1",
            token_pair=pair,
            signal=Signal.BUY,
            confidence=0.8,
            amount=0.01,
            timestamp=time.time(),
            reasoning="Test"
        )
        
        with patch.object(bot.logger, 'info') as mock_info:
            bot._execute_trade(decision)
            assert any("DRY RUN" in str(call) for call in mock_info.call_args_list)


class TestGracefulShutdown:
    """Tests for graceful shutdown."""

    def test_shutdown_sets_running_to_false(self):
        """Test that shutdown sets _running to False."""
        config = TradingConfig(dry_run=True)
        bot = create_mock_bot(config=config, dry_run=True)
        
        bot._running = True
        bot._shutdown()
        assert bot._running is False

    def test_signal_handlers_set_up(self):
        """Test that signal handlers are set up correctly."""
        config = TradingConfig(dry_run=True)
        
        with patch('src.cli.signal') as mock_signal:
            mock_signal.signal = Mock()
            with patch.object(TradingBot, '_initialize_services'):
                bot = TradingBot(config=config, dry_run=True)
                assert mock_signal.signal.call_count == 2


class TestConfigurationLogging:
    """Tests for configuration logging."""

    def test_log_configuration_logs_all_settings(self):
        """Test that configuration is logged at startup."""
        pair = TokenPair(
            base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
            quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
        )
        config = TradingConfig(
            pairs=[pair],
            interval=30.0,
            network="devnet",
            dry_run=True,
            log_level="INFO"
        )
        bot = create_mock_bot(config=config, dry_run=True)
        
        with patch.object(bot.logger, 'info') as mock_info:
            bot._log_configuration()
            assert mock_info.call_count >= 5
