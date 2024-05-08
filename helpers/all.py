# IMPORTS
import inferences


# INDICATOR PERIODS
MA_RSI_PERIOD = 14
BOLLINGER_PERIOD = 20
MACD_SIGNAL_PERIOD = 9
MACD_SHORT_PERIOD = 12
MACD_LONG_PERIOD = 26
BOLLINGER_N_STD = 2


def rsi(data, window = MA_RSI_PERIOD, modify = True):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    if modify:
      data["rsi"] = rsi
      return data
    else:
      return rsi


def sma(data, window = MA_RSI_PERIOD, modify = True):
    _sma = data['close'].rolling(window=window).mean()

    if modify:
      data["sma"] = _sma
      return data
    else:
      return _sma


def ema(data, span = MA_RSI_PERIOD, modify = True):
    _ema = data['close'].ewm(span=span, adjust=False).mean()

    if modify:
      data["ema"] = _ema
      return data
    else:
      return _ema


def stochastic_oscillator(data, window = MA_RSI_PERIOD, modify = True):
    lowest_low = data['low'].rolling(window=window).min()
    highest_high = data['high'].rolling(window=window).max()
    _stochastic = ((data['close'] - lowest_low) / (highest_high - lowest_low)) * 100

    if modify:
      data["stochastic"] = _stochastic
      return data
    else:
      return _stochastic


def bollinger_bands(data, window = BOLLINGER_PERIOD, num_std = 2, modify = True):
    rolling_mean = data['close'].rolling(window=window).mean()
    rolling_std = data['close'].rolling(window=window).std()

    _lower_band = rolling_mean - (rolling_std * num_std)
    _upper_band = rolling_mean + (rolling_std * num_std)

    if modify:
      data["bollinger_lower"] = _lower_band
      data["bollinger_upper"] = _upper_band
      return data
    else:
      return _lower_band, _upper_band


def macd(data, short_window = MACD_SHORT_PERIOD, long_window = MACD_LONG_PERIOD, signal_window = MACD_SIGNAL_PERIOD, modify = True):
    _ema_short = ema(data, span=short_window, modify=False)
    _ema_long = ema(data, span=long_window, modify=False)

    macd_line = _ema_short - _ema_long
    signal_line = macd_line.rolling(window=signal_window).mean()

    if modify:
      data["macd"] = macd_line
      data["macd_signal"] = signal_line
      return data
    else:
      return macd_line, signal_line


def to_lowercase_columns(data):
    data.columns = [column.replace(" ", "_").lower() for column in data.columns]
    return data


def append_technical_indicators(data, add_outcomes = True):
    data = data.astype(float)
    # data = to_lowercase_columns(data)
    data = rsi(data)
    data = sma(data)
    data = ema(data)
    data = stochastic_oscillator(data)
    data = bollinger_bands(data)
    data = macd(data)
    data = data.dropna().drop_duplicates()

    # OUTCOMES OF THE TICKER
    if add_outcomes:
        data["buy_sell"] = (data.open - data.close > 0).apply(lambda x: 1 if x > 0 else 0)
    return data