"""Pitch and resonance analysis module.

Analyzes audio using praat-parselmouth for pitch and librosa for resonance.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
import parselmouth
from parselmouth.praat import call


def extract_pitch_from_audio(audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
    """Extract pitch from audio data using praat-parselmouth.
    
    Args:
        audio_data: Audio signal as numpy array
        sample_rate: Sample rate in Hz
        
    Returns:
        Dictionary containing pitch analysis results
    """
    try:
        # Create Sound object from audio data
        sound = parselmouth.Sound(audio_data, sampling_frequency=sample_rate)
        
        # Extract pitch using praat
        pitch = call(sound, "To Pitch", 0.01, 75, 600)  # time_step, f_min, f_max
        
        # Get pitch values
        pitch_values = pitch.selected_array['frequency']
        pitch_values[pitch_values == 0] = np.nan  # Replace unvoiced parts with NaN
        
        # Calculate statistics
        valid_pitches = pitch_values[~np.isnan(pitch_values)]
        
        if len(valid_pitches) > 0:
            median_pitch = np.median(valid_pitches)
            mean_pitch = np.mean(valid_pitches)
            min_pitch = np.min(valid_pitches)
            max_pitch = np.max(valid_pitches)
            std_pitch = np.std(valid_pitches)
        else:
            median_pitch = mean_pitch = min_pitch = max_pitch = std_pitch = 0.0
        
        return {
            'median_pitch': median_pitch,
            'mean_pitch': mean_pitch,
            'min_pitch': min_pitch,
            'max_pitch': max_pitch,
            'std_pitch': std_pitch,
            'voiced_frames': len(valid_pitches),
            'total_frames': len(pitch_values),
            'voicing_rate': len(valid_pitches) / len(pitch_values) if len(pitch_values) > 0 else 0
        }
        
    except Exception as e:
        # Return zero values if pitch extraction fails
        return {
            'median_pitch': 0.0,
            'mean_pitch': 0.0,
            'min_pitch': 0.0,
            'max_pitch': 0.0,
            'std_pitch': 0.0,
            'voiced_frames': 0,
            'total_frames': 0,
            'voicing_rate': 0.0,
            'error': str(e)
        }


def extract_resonance_from_audio(audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
    """Extract resonance (formants) from audio data using librosa.
    
    Uses Linear Predictive Coding (LPC) to estimate formant frequencies.
    Formants are important for understanding voice resonance characteristics.
    
    Args:
        audio_data: Audio signal as numpy array
        sample_rate: Sample rate in Hz
        
    Returns:
        Dictionary containing resonance analysis results with formant frequencies
    """
    try:
        import librosa
        
        # Ensure audio is mono and proper dtype
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        audio_data = audio_data.astype(np.float64)
        
        # Use LPC-based formant estimation
        # Formant estimation using linear prediction
        frame_length = 2048
        hop_length = 512
        
        # Calculate number of frames
        n_frames = (len(audio_data) - frame_length) // hop_length + 1
        
        if n_frames < 1:
            return _empty_resonance_result()
        
        # Estimate formants for each frame
        f1_values = []
        f2_values = []
        f3_values = []
        
        for i in range(n_frames):
            start = i * hop_length
            end = start + frame_length
            
            if end > len(audio_data):
                break
                
            frame = audio_data[start:end]
            
            # Apply window
            windowed = frame * np.hanning(frame_length)
            
            try:
                # Use LPC to estimate formants
                # Number of formants to estimate (we want F1, F2, F3)
                # For voice, typically 8-12 LPC coefficients for 3 formants
                lpc_order = 12
                
                # Compute LPC coefficients
                lpc_coeffs = librosa.lpc(windowed, order=lpc_order)
                
                # Find roots of LPC polynomial (formant frequencies)
                roots = np.roots(lpc_coeffs)
                
                # Keep only roots in upper half of unit circle (positive frequencies)
                roots = roots[np.imag(roots) >= 0]
                
                # Convert to frequencies
                frequencies = np.arctan2(np.imag(roots), np.real(roots))
                frequencies = frequencies * sample_rate / (2 * np.pi)
                
                # Sort and take first 3 formants (lowest frequencies)
                frequencies = np.sort(frequencies[frequencies > 0])
                
                if len(frequencies) >= 3:
                    f1_values.append(frequencies[0])
                    f2_values.append(frequencies[1])
                    f3_values.append(frequencies[2])
                elif len(frequencies) >= 2:
                    f1_values.append(frequencies[0])
                    f2_values.append(frequencies[1])
                    f3_values.append(frequencies[1])  # Use F2 for F3
                elif len(frequencies) >= 1:
                    f1_values.append(frequencies[0])
                    f2_values.append(frequencies[0])
                    f3_values.append(frequencies[0])
                    
            except Exception:
                # If LPC fails for this frame, skip it
                continue
        
        # Calculate statistics if we have valid formant values
        if len(f1_values) > 0:
            f1_array = np.array(f1_values)
            f2_array = np.array(f2_values)
            f3_array = np.array(f3_values)
            
            # Filter out unrealistic formant values
            # Typical formant ranges: F1=200-1000Hz, F2=800-2500Hz, F3=2000-3500Hz
            valid_f1 = f1_array[(f1_array >= 200) & (f1_array <= 1200)]
            valid_f2 = f2_array[(f2_array >= 700) & (f2_array <= 2800)]
            valid_f3 = f3_array[(f3_array >= 1500) & (f3_array <= 3800)]
            
            return {
                'f1_mean': float(np.mean(valid_f1)) if len(valid_f1) > 0 else 0.0,
                'f2_mean': float(np.mean(valid_f2)) if len(valid_f2) > 0 else 0.0,
                'f3_mean': float(np.mean(valid_f3)) if len(valid_f3) > 0 else 0.0,
                'f1_std': float(np.std(valid_f1)) if len(valid_f1) > 1 else 0.0,
                'f2_std': float(np.std(valid_f2)) if len(valid_f2) > 1 else 0.0,
                'f3_std': float(np.std(valid_f3)) if len(valid_f3) > 1 else 0.0,
                'formant_placeholder': False,
                'formant_frames_analyzed': len(f1_values),
                'formant_valid_frames': len(valid_f1),
            }
        else:
            return _empty_resonance_result()
        
    except ImportError:
        # librosa not available
        return _empty_resonance_result()
        
    except Exception as e:
        return {
            'f1_mean': 0.0,
            'f2_mean': 0.0,
            'f3_mean': 0.0,
            'f1_std': 0.0,
            'f2_std': 0.0,
            'f3_std': 0.0,
            'formant_placeholder': False,
            'error': str(e)
        }


def _empty_resonance_result() -> Dict[str, Any]:
    """Return an empty resonance result."""
    return {
        'f1_mean': 0.0,
        'f2_mean': 0.0,
        'f3_mean': 0.0,
        'f1_std': 0.0,
        'f2_std': 0.0,
        'f3_std': 0.0,
        'formant_placeholder': False,
        'formant_frames_analyzed': 0,
    }


def extract_full_analysis(audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
    """Extract both pitch and resonance from audio data.
    
    Args:
        audio_data: Audio signal as numpy array
        sample_rate: Sample rate in Hz
        
    Returns:
        Dictionary containing complete analysis results
    """
    pitch_result = extract_pitch_from_audio(audio_data, sample_rate)
    resonance_result = extract_resonance_from_audio(audio_data, sample_rate)
    
    # Merge results
    result = {
        # Pitch data
        'median_pitch': pitch_result.get('median_pitch', 0.0),
        'mean_pitch': pitch_result.get('mean_pitch', 0.0),
        'min_pitch': pitch_result.get('min_pitch', 0.0),
        'max_pitch': pitch_result.get('max_pitch', 0.0),
        'std_pitch': pitch_result.get('std_pitch', 0.0),
        'voiced_frames': pitch_result.get('voiced_frames', 0),
        'total_frames': pitch_result.get('total_frames', 0),
        'voicing_rate': pitch_result.get('voicing_rate', 0.0),
        
        # Resonance data
        'f1_mean': resonance_result.get('f1_mean', 0.0),
        'f2_mean': resonance_result.get('f2_mean', 0.0),
        'f3_mean': resonance_result.get('f3_mean', 0.0),
        'f1_std': resonance_result.get('f1_std', 0.0),
        'f2_std': resonance_result.get('f2_std', 0.0),
        'f3_std': resonance_result.get('f3_std', 0.0),
        'formant_placeholder': resonance_result.get('formant_placeholder', True),
        
        # Metadata
        'sample_rate': sample_rate,
        'duration_seconds': len(audio_data) / sample_rate if len(audio_data) > 0 else 0.0,
    }
    
    # Include any errors
    if 'error' in pitch_result:
        result['pitch_error'] = pitch_result['error']
    if 'error' in resonance_result:
        result['resonance_error'] = resonance_result['error']
    
    return result


def check_pitch_in_target(pitch: float, target_min: float, target_max: float) -> Tuple[bool, float]:
    """Check if a pitch value is within target range.
    
    Args:
        pitch: Pitch value in Hz
        target_min: Minimum of target range in Hz
        target_max: Maximum of target range in Hz
        
    Returns:
        Tuple of (is_in_range, deviation_from_center)
    """
    if pitch <= 0:
        return False, 0.0
    
    center = (target_min + target_max) / 2
    deviation = (pitch - center) / center * 100  # Percentage from center
    
    return target_min <= pitch <= target_max, deviation
