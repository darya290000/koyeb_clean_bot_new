"""
تشخیص سیگنال‌های معاملاتی پیشرفته
"""
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvancedSignalDetector:
    """تشخیص سیگنال‌های معاملاتی حرفه‌ای"""
    
    def __init__(self, config):
        self.config = config
        self.min_profit = config.MIN_PROFIT_PERCENTAGE
        self.stop_loss = config.STOP_LOSS_PERCENTAGE
        self.validity_candles = config.SIGNAL_VALIDITY_CANDLES
        self.swing_left = config.SWING_LEFT
        self.swing_right = config.SWING_RIGHT
        
        logger.info("🎯 سیستم تشخیص سیگنال آماده شد")
    
    def detect_all_signals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """تشخیص تمام انواع سیگنال‌ها"""
        try:
            if len(df) < 100:
                logger.warning("⚠️ داده‌های ناکافی برای تحلیل")
                return []
            
            # تشخیص swing points
            df = self._detect_swing_points(df)
            
            all_signals = []
            
            # BOS/CHoCH signals
            bos_signals, choch_signals = self._detect_market_structure(df)
            all_signals.extend(bos_signals)
            all_signals.extend(choch_signals)
            
            # Fair Value Gap signals
            fvg_signals = self._detect_fair_value_gaps(df)
            all_signals.extend(fvg_signals)
            
            # EMA Cross signals
            ema_signals = self._detect_ema_signals(df)
            all_signals.extend(ema_signals)
            
            # Order Block signals
            ob_signals = self._detect_order_blocks(df)
            all_signals.extend(ob_signals)
            
            # Liquidity signals
            liquidity_signals = self._detect_liquidity_grabs(df)
            all_signals.extend(liquidity_signals)
            
            # فیلتر و مرتب‌سازی
            filtered_signals = self._filter_signals(all_signals, df)
            
            logger.info(f"🎯 {len(filtered_signals)} سیگنال معتبر تشخیص داده شد")
            return filtered_signals
            
        except Exception as e:
            logger.error(f"❌ خطا در تشخیص سیگنال‌ها: {e}")
            return []
    
    def _detect_swing_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """تشخیص نقاط swing با دقت بالا"""
        if len(df) < (self.swing_left + self.swing_right + 1):
            df['Swing_High'] = False
            df['Swing_Low'] = False
            return df
        
        swing_high = []
        swing_low = []
        
        for i in range(len(df)):
            if i < self.swing_left or i > len(df) - self.swing_right - 1:
                swing_high.append(False)
                swing_low.append(False)
                continue
            
            try:
                # بررسی swing high
                left_highs = df['high'][i-self.swing_left:i].tolist()
                right_highs = df['high'][i+1:i+self.swing_right+1].tolist()
                current_high = df['high'].iloc[i]
                
                is_swing_high = (
                    all(current_high >= h for h in left_highs) and
                    all(current_high >= h for h in right_highs) and
                    current_high > max(left_highs + right_highs, default=0)
                )
                
                # بررسی swing low
                left_lows = df['low'][i-self.swing_left:i].tolist()
                right_lows = df['low'][i+1:i+self.swing_right+1].tolist()
                current_low = df['low'].iloc[i]
                
                is_swing_low = (
                    all(current_low <= l for l in left_lows) and
                    all(current_low <= l for l in right_lows) and
                    current_low < min(left_lows + right_lows, default=float('inf'))
                )
                
                swing_high.append(is_swing_high)
                swing_low.append(is_swing_low)
                
            except Exception as e:
                logger.error(f"خطا در تشخیص swing point: {e}")
                swing_high.append(False)
                swing_low.append(False)
        
        df['Swing_High'] = swing_high
        df['Swing_Low'] = swing_low
        return df
    
    def _detect_market_structure(self, df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
        """تشخیص BOS و CHoCH با دقت بالا"""
        bos_signals = []
        choch_signals = []
        
        try:
            swing_highs = df[df['Swing_High']].copy()
            swing_lows = df[df['Swing_Low']].copy()
            
            if len(swing_highs) < 2 or len(swing_lows) < 2:
                return bos_signals, choch_signals
            
            # تشخیص BOS صعودی (شکست آخرین سقف)
            for i, (idx, row) in enumerate(swing_highs.iterrows()):
                if i == len(swing_highs) - 1:  # آخرین سقف
                    continue
                    
                high_level = row['high']
                
                # جستجو برای شکست این سطح
                for j in range(idx + 1, min(len(df), len(df) - self.validity_candles)):
                    if df.loc[j, 'close'] > high_level:
                        # تأیید شکست با حجم
                        volume_confirmation = self._check_volume_confirmation(df, j)
                        
                        profitability = self._calculate_signal_profitability(df, j, 'BUY')
                        if profitability and profitability['is_profitable']:
                            signal = {
                                'index': j,
                                'timestamp': df.loc[j, 'timestamp'],
                                'type': 'BOS_BULLISH',
                                'entry_price': df.loc[j, 'close'],
                                'broken_level': high_level,
                                'strength': self._calculate_signal_strength(df, j, 'bullish'),
                                'volume_confirmed': volume_confirmation,
                                'profitability': profitability
                            }
                            bos_signals.append(signal)
                        break
            
            # تشخیص CHoCH نزولی (شکست آخرین کف)
            for i, (idx, row) in enumerate(swing_lows.iterrows()):
                if i == len(swing_lows) - 1:  # آخرین کف
                    continue
                    
                low_level = row['low']
                
                # جستجو برای شکست این سطح
                for j in range(idx + 1, min(len(df), len(df) - self.validity_candles)):
                    if df.loc[j, 'close'] < low_level:
                        volume_confirmation = self._check_volume_confirmation(df, j)
                        
                        profitability = self._calculate_signal_profitability(df, j, 'SELL')
                        if profitability and profitability['is_profitable']:
                            signal = {
                                'index': j,
                                'timestamp': df.loc[j, 'timestamp'],
                                'type': 'CHOCH_BEARISH',
                                'entry_price': df.loc[j, 'close'],
                                'broken_level': low_level,
                                'strength': self._calculate_signal_strength(df, j, 'bearish'),
                                'volume_confirmed': volume_confirmation,
                                'profitability': profitability
                            }
                            choch_signals.append(signal)
                        break
            
        except Exception as e:
            logger.error(f"خطا در تشخیص market structure: {e}")
        
        return bos_signals, choch_signals
    
    def _detect_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """تشخیص Fair Value Gaps پیشرفته"""
        fvg_signals = []
        
        try:
            for i in range(2, len(df) - self.validity_candles):
                prev2_high = df['high'].iloc[i-2]
                prev2_low = df['low'].iloc[i-2]
                prev1_high = df['high'].iloc[i-1]
                prev1_low = df['low'].iloc[i-1]
                current_high = df['high'].iloc[i]
                current_low = df['low'].iloc[i]
                
                # بررسی گپ صعودی
                if current_low > prev2_high and prev1_low > prev2_high:
                    gap_size = (current_low - prev2_high) / prev2_high * 100
                    
                    if gap_size >= self.config.MIN_GAP_PERCENTAGE:
                        # تأیید با حجم
                        volume_spike = df['volume'].iloc[i] > df['volume'].iloc[i-5:i].mean() * 1.5
                        
                        profitability = self._calculate_signal_profitability(df, i, 'BUY')
                        if profitability and profitability['is_profitable']:
                            signal = {
                                'index': i,
                                'timestamp': df['timestamp'].iloc[i],
                                'type': 'FVG_BULLISH',
                                'entry_price': df['close'].iloc[i],
                                'gap_size': gap_size,
                                'gap_range': (prev2_high, current_low),
                                'volume_spike': volume_spike,
                                'strength': min(gap_size / 0.5, 5.0),  # نرمال‌سازی قدرت
                                'profitability': profitability
                            }
                            fvg_signals.append(signal)
                
                # بررسی گپ نزولی
                elif current_high < prev2_low and prev1_high < prev2_low:
                    gap_size = (prev2_low - current_high) / current_high * 100
                    
                    if gap_size >= self.config.MIN_GAP_PERCENTAGE:
                        volume_spike = df['volume'].iloc[i] > df['volume'].iloc[i-5:i].mean() * 1.5
                        
                        profitability = self._calculate_signal_profitability(df, i, 'SELL')
                        if profitability and profitability['is_profitable']:
                            signal = {
                                'index': i,
                                'timestamp': df['timestamp'].iloc[i],
                                'type': 'FVG_BEARISH',
                                'entry_price': df['close'].iloc[i],
                                'gap_size': gap_size,
                                'gap_range': (current_high, prev2_low),
                                'volume_spike': volume_spike,
                                'strength': min(gap_size / 0.5, 5.0),
                                'profitability': profitability
                            }
                            fvg_signals.append(signal)
        
        except Exception as e:
            logger.error(f"خطا در تشخیص FVG: {e}")
        
        return fvg_signals
    
    def _detect_ema_signals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """تشخیص سیگنال‌های EMA با فیلترهای پیشرفته"""
        ema_signals = []
        
        try:
            # محاسبه EMA ها
            df['EMA_20'] = df['close'].ewm(span=self.config.EMA_FAST).mean()
            df['EMA_50'] = df['close'].ewm(span=self.config.EMA_SLOW).mean()
            
            for i in range(self.config.EMA_SLOW, len(df) - self.validity_candles):
                current_20 = df['EMA_20'].iloc[i]
                current_50 = df['EMA_50'].iloc[i]
                prev_20 = df['EMA_20'].iloc[i-1]
                prev_50 = df['EMA_50'].iloc[i-1]
                
                signal_type = None
                signal_name = ''
                
                # کراس صعودی با تأیید trend
                if (current_20 > current_50 and prev_20 <= prev_50 and
                    self._confirm_trend_direction(df, i, 'bullish')):
                    signal_type = 'BUY'
                    signal_name = 'EMA_CROSS_BULLISH'
                
                # کراس نزولی با تأیید trend
                elif (current_20 < current_50 and prev_20 >= prev_50 and
                      self._confirm_trend_direction(df, i, 'bearish')):
                    signal_type = 'SELL'
                    signal_name = 'EMA_CROSS_BEARISH'
                
                if signal_type:
                    # محاسبه قدرت سیگنال
                    strength = abs(current_20 - current_50) / current_50 * 100
                    
                    profitability = self._calculate_signal_profitability(df, i, signal_type)
                    if profitability and profitability['is_profitable']:
                        signal = {
                            'index': i,
                            'timestamp': df['timestamp'].iloc[i],
                            'type': signal_name,
                            'entry_price': df['close'].iloc[i],
                            'ema20': current_20,
                            'ema50': current_50,
                            'strength': min(strength, 5.0),
                            'profitability': profitability
                        }
                        ema_signals.append(signal)
        
        except Exception as e:
            logger.error(f"خطا در تشخیص EMA signals: {e}")
        
        return ema_signals
    
    def _detect_order_blocks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """تشخیص Order Blocks"""
        ob_signals = []
        
        try:
            for i in range(20, len(df) - self.validity_candles):
                # بررسی Order Block صعودی
                if self._is_bullish_order_block(df, i):
                    profitability = self._calculate_signal_profitability(df, i, 'BUY')
                    if profitability and profitability['is_profitable']:
                        signal = {
                            'index': i,
                            'timestamp': df['timestamp'].iloc[i],
                            'type': 'ORDER_BLOCK_BULLISH',
                            'entry_price': df['close'].iloc[i],
                            'ob_range': (df['low'].iloc[i-3:i+1].min(), df['high'].iloc[i-3:i+1].max()),
                            'strength': self._calculate_signal_strength(df, i, 'bullish'),
                            'profitability': profitability
                        }
                        ob_signals.append(signal)
                
                # بررسی Order Block نزولی
                elif self._is_bearish_order_block(df, i):
                    profitability = self._calculate_signal_profitability(df, i, 'SELL')
                    if profitability and profitability['is_profitable']:
                        signal = {
                            'index': i,
                            'timestamp': df['timestamp'].iloc[i],
                            'type': 'ORDER_BLOCK_BEARISH',
                            'entry_price': df['close'].iloc[i],
                            'ob_range': (df['low'].iloc[i-3:i+1].min(), df['high'].iloc[i-3:i+1].max()),
                            'strength': self._calculate_signal_strength(df, i, 'bearish'),
                            'profitability': profitability
                        }
                        ob_signals.append(signal)
        
        except Exception as e:
            logger.error(f"خطا در تشخیص Order Blocks: {e}")
        
        return ob_signals
    
    def _detect_liquidity_grabs(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """تشخیص Liquidity Grabs"""
        liquidity_signals = []
        
        try:
            # تشخیص سطوح liquidity (highs/lows اخیر)
            recent_highs = df[df['Swing_High']].tail(10)
            recent_lows = df[df['Swing_Low']].tail(10)
            
            for i in range(50, len(df) - self.validity_candles):
                current_high = df['high'].iloc[i]
                current_low = df['low'].iloc[i]
                
                # بررسی grab بالای liquidity
                for _, high_row in recent_highs.iterrows():
                    if (current_high > high_row['high'] * 1.001 and  # شکست با مارژین
                        df['close'].iloc[i] < high_row['high']):  # اما close زیر سطح
                        
                        profitability = self._calculate_signal_profitability(df, i, 'SELL')
                        if profitability and profitability['is_profitable']:
                            signal = {
                                'index': i,
                                'timestamp': df['timestamp'].iloc[i],
                                'type': 'LIQUIDITY_GRAB_BEARISH',
                                'entry_price': df['close'].iloc[i],
                                'grabbed_level': high_row['high'],
                                'strength': 3.0,
                                'profitability': profitability
                            }
                            liquidity_signals.append(signal)
                        break
                
                # بررسی grab پایین liquidity
                for _, low_row in recent_lows.iterrows():
                    if (current_low < low_row['low'] * 0.999 and  # شکست با مارژین
                        df['close'].iloc[i] > low_row['low']):  # اما close بالای سطح
                        
                        profitability = self._calculate_signal_profitability(df, i, 'BUY')
                        if profitability and profitability['is_profitable']:
                            signal = {
                                'index': i,
                                'timestamp': df['timestamp'].iloc[i],
                                'type': 'LIQUIDITY_GRAB_BULLISH',
                                'entry_price': df['close'].iloc[i],
                                'grabbed_level': low_row['low'],
                                'strength': 3.0,
                                'profitability': profitability
                            }
                            liquidity_signals.append(signal)
                        break
        
        except Exception as e:
            logger.error(f"خطا در تشخیص Liquidity Grabs: {e}")
        
        return liquidity_signals
    
    def _calculate_signal_profitability(self, df: pd.DataFrame, signal_index: int, 
                                      signal_type: str) -> Optional[Dict[str, Any]]:
        """محاسبه دقیق سودآوری سیگنال"""
        try:
            if signal_index >= len(df) - self.validity_candles:
                return None
            
            entry_price = df['close'].iloc[signal_index]
            max_profit = 0
            max_loss = 0
            hit_target = False
            hit_stop = False
            
            # محاسبه target و stop loss
            if signal_type == 'BUY':
                target_price = entry_price * (1 + self.min_profit / 100)
                stop_price = entry_price * (1 - self.stop_loss / 100)
            else:  # SELL
                target_price = entry_price * (1 - self.min_profit / 100)
                stop_price = entry_price * (1 + self.stop_loss / 100)
            
            # بررسی کندل‌های بعدی
            for i in range(signal_index + 1, min(signal_index + self.validity_candles + 1, len(df))):
                high_price = df['high'].iloc[i]
                low_price = df['low'].iloc[i]
                
                if signal_type == 'BUY':
                    # بررسی target و stop
                    if high_price >= target_price:
                        hit_target = True
                    if low_price <= stop_price:
                        hit_stop = True
                    
                    profit = (high_price - entry_price) / entry_price * 100
                    loss = (low_price - entry_price) / entry_price * 100
                else:  # SELL
                    if low_price <= target_price:
                        hit_target = True
                    if high_price >= stop_price:
                        hit_stop = True
                    
                    profit = (entry_price - low_price) / entry_price * 100
                    loss = (entry_price - high_price) / entry_price * 100
                
                max_profit = max(max_profit, profit)
                max_loss = min(max_loss, loss)
            
            # محاسبه Risk/Reward
            risk_reward = max_profit / abs(max_loss) if max_loss != 0 else float('inf')
            
            return {
                'max_profit': max_profit,
                'max_loss': max_loss,
                'is_profitable': max_profit >= self.min_profit,
                'risk_reward': risk_reward,
                'hit_target': hit_target,
                'hit_stop': hit_stop,
                'entry_price': entry_price,
                'target_price': target_price,
                'stop_price': stop_price
            }
            
        except Exception as e:
            logger.error(f"خطا در محاسبه سودآوری: {e}")
            return None
    
    def _filter_signals(self, signals: List[Dict[str, Any]], df: pd.DataFrame) -> List[Dict[str, Any]]:
        """فیلتر و رتبه‌بندی سیگنال‌های با کیفیت"""
        try:
            # فیلتر سیگنال‌های سودآور
            profitable_signals = [s for s in signals if s['profitability']['is_profitable']]
            
            # مرتب‌سازی بر اساس کیفیت
            def signal_quality_score(signal):
                prof = signal['profitability']
                base_score = prof['risk_reward'] * signal.get('strength', 1.0)
                
                # بونوس برای تأیید حجم
                if signal.get('volume_confirmed', False):
                    base_score *= 1.2
                
                # بونوس برای سیگنال‌های اخیر
                recency_bonus = max(0, (len(df) - signal['index']) / 10)
                base_score += recency_bonus
                
                return base_score
            
            profitable_signals.sort(key=signal_quality_score, reverse=True)
            
            # محدود کردن تعداد سیگنال‌ها
            return profitable_signals[:10]  # حداکثر 10 سیگنال برتر
            
        except Exception as e:
            logger.error(f"خطا در فیلتر سیگنال‌ها: {e}")
            return signals
    
    def _check_volume_confirmation(self, df: pd.DataFrame, index: int) -> bool:
        """بررسی تأیید حجم"""
        try:
            current_volume = df['volume'].iloc[index]
            avg_volume = df['volume'].iloc[max(0, index-20):index].mean()
            return current_volume > avg_volume * 1.5
        except:
            return False
    
    def _calculate_signal_strength(self, df: pd.DataFrame, index: int, direction: str) -> float:
        """محاسبه قدرت سیگنال"""
        try:
            strength = 1.0
            
            # قدرت بر اساس حجم
            if self._check_volume_confirmation(df, index):
                strength += 1.0
            
            # قدرت بر اساس momentum
            price_change = df['close'].iloc[index] / df['close'].iloc[index-5] - 1
            if (direction == 'bullish' and price_change > 0) or (direction == 'bearish' and price_change < 0):
                strength += abs(price_change) * 100
            
            return min(strength, 5.0)  # حداکثر 5
            
        except:
            return 1.0
    
    def _confirm_trend_direction(self, df: pd.DataFrame, index: int, direction: str) -> bool:
        """تأیید جهت trend"""
        try:
            if 'EMA_200' not in df.columns:
                return True  # اگر EMA200 نداریم، تأیید می‌کنیم
            
            current_price = df['close'].iloc[index]
            ema_200 = df['EMA_200'].iloc[index]
            
            if direction == 'bullish':
                return current_price > ema_200
            else:
                return current_price < ema_200
                
        except:
            return True
    
    def _is_bullish_order_block(self, df: pd.DataFrame, index: int) -> bool:
        """تشخیص Order Block صعودی"""
        try:
            # منطق ساده: کندل سبز قوی بعد از چند کندل قرمز
            recent_candles = df.iloc[index-5:index+1]
            red_candles = (recent_candles['close'] < recent_candles['open']).sum()
            current_green = df['close'].iloc[index] > df['open'].iloc[index]
            strong_green = (df['close'].iloc[index] - df['open'].iloc[index]) / df['open'].iloc[index] > 0.02
            
            return red_candles >= 3 and current_green and strong_green
        except:
            return False
    
    def _is_bearish_order_block(self, df: pd.DataFrame, index: int) -> bool:
        """تشخیص Order Block نزولی"""
        try:
            recent_candles = df.iloc[index-5:index+1]
            green_candles = (recent_candles['close'] > recent_candles['open']).sum()
            current_red = df['close'].iloc[index] < df['open'].iloc[index]
            strong_red = (df['open'].iloc[index] - df['close'].iloc[index]) / df['open'].iloc[index] > 0.02
            
            return green_candles >= 3 and current_red and strong_red
        except:
            return False
        # ...existing code...

# داده تستی با روند صعودی و نزولی
prices = [100 + i*0.5 if i < 60 else 130 - (i-60)*0.7 for i in range(120)]
df = pd.DataFrame({
    'timestamp': pd.date_range(start='2024-01-01', periods=120, freq='D'),
    'open': prices,
    'high': [p + 1 for p in prices],
    'low': [p - 1 for p in prices],
    'close': prices,
    'volume': np.random.randint(100, 1000, 120)
})

class Config:
    MIN_PROFIT_PERCENTAGE = 1.5
    STOP_LOSS_PERCENTAGE = 1.0
    SIGNAL_VALIDITY_CANDLES = 10
    SWING_LEFT = 3
    SWING_RIGHT = 3
    MIN_GAP_PERCENTAGE = 0.5
    EMA_FAST = 20
    EMA_SLOW = 50

if __name__ == "__main__":
    detector = AdvancedSignalDetector(Config())
    signals = detector.detect_all_signals(df)

    if signals:
        print(f"\n📊 {len(signals)} سیگنال معتبر یافت شد:\n")
        for i, s in enumerate(signals, 1):
            print(f"{i:02d}) {s['timestamp']} | {s['type']} | "
                  f"Entry: {s['entry_price']:.2f} | "
                  f"Strength: {s['strength']:.2f} | "
                  f"Profit: {s['profitability']['max_profit']:.2f}% | "
                  f"RR: {s['profitability']['risk_reward']:.2f}")
    else:
        print("⚠️ هیچ سیگنالی پیدا نشد.")
# ...existing code...
if signals:
    for i, s in enumerate(signals, 1):
        signal_text = (
            f"{i:02d}) {s['timestamp']} | {s['type']} | "
            f"Entry: {s['entry_price']:.2f} | "
            f"Strength: {s['strength']:.2f} | "
            f"Profit: {s['profitability']['max_profit']:.2f}% | "
            f"RR: {s['profitability']['risk_reward']:.2f}"
        )
        # اینجا به جای print، سیگنال را به ربات بفرست
        print(signal_text)
else:
    print("⚠️ هیچ سیگنالی پیدا نشد.")