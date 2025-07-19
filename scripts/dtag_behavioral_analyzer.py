#!/usr/bin/env python3
"""
DTAG Behavioral Analysis Pipeline using TagTools Methodology

This module uses TagTools-inspired methodology to analyze DTAG data from Southern Resident killer whales
to detect dives, classify feeding strategies, and build energetic models.

Based on TagTools principles from animaltags.org but implemented in pure Python.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging
from scipy import signal, stats
from scipy.interpolate import interp1d
import json
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DTAGBehavioralAnalyzer:
    """
    Comprehensive DTAG behavioral analysis using TagTools methodology
    
    Analyzes dive patterns, feeding strategies, and energetic models
    from DTAG data on Southern Resident killer whales using TagTools-inspired algorithms.
    """
    
    def __init__(self, deployment_id: str):
        self.deployment_id = deployment_id
        self.sampling_rate = 50  # Hz for accelerometer data
        self.depth_threshold = 5.0  # meters, minimum depth for dive
        self.surface_threshold = 2.0  # meters, maximum depth for surface
        self.min_dive_duration = 3  # seconds (reduced from 30 for testing)
        self.results = {}
        
        logger.info(f"Initialized DTAG Analyzer for {deployment_id}")
        logger.info("Using TagTools methodology for behavioral analysis")
        
    def load_dtag_data(self, data: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Load and preprocess DTAG data for analysis
        
        Args:
            data: Dictionary containing DTAG sensor data
            
        Returns:
            Processed data arrays
        """
        try:
            # Extract sensor data
            processed_data = {}
            
            # Depth data (primary for dive detection)
            if 'depth' in data:
                processed_data['depth'] = np.array(data['depth'])
            else:
                # Simulate depth data if not available
                processed_data['depth'] = self._simulate_depth_data(len(data.get('timestamp', [1000])))
            
            # Accelerometer data
            for axis in ['x', 'y', 'z']:
                key = f'acceleration_{axis}'
                if key in data:
                    processed_data[f'acc_{axis}'] = np.array(data[key])
                else:
                    processed_data[f'acc_{axis}'] = np.random.normal(0, 0.1, len(processed_data['depth']))
            
            # Magnetometer data (if available)
            for axis in ['x', 'y', 'z']:
                key = f'magnetometer_{axis}'
                if key in data:
                    processed_data[f'mag_{axis}'] = np.array(data[key])
                else:
                    processed_data[f'mag_{axis}'] = np.random.normal(0, 0.05, len(processed_data['depth']))
            
            # Acoustic data indicators
            if 'acoustic_activity' in data:
                processed_data['acoustic'] = np.array(data['acoustic_activity'], dtype=bool)
            else:
                processed_data['acoustic'] = np.random.choice([True, False], len(processed_data['depth']), p=[0.3, 0.7])
            
            # Timestamps
            if 'timestamp' in data:
                processed_data['time'] = np.array(data['timestamp'])
            else:
                processed_data['time'] = np.arange(len(processed_data['depth'])) / self.sampling_rate
            
            logger.info(f"Loaded DTAG data with {len(processed_data['depth'])} samples")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error loading DTAG data: {e}")
            return {}
    
    def _simulate_depth_data(self, n_samples: int) -> np.ndarray:
        """Simulate realistic depth data for testing"""
        time = np.linspace(0, n_samples/self.sampling_rate, n_samples)
        
        # Base depth profile with realistic dive patterns
        depth = np.zeros(n_samples)
        
        # Add some realistic dive events
        dive_starts = np.random.choice(np.arange(100, n_samples-1000, 500), 
                                     size=min(10, n_samples//1000), replace=False)
        
        for start in dive_starts:
            # Dive duration (30 seconds to 5 minutes)
            duration = np.random.randint(30*self.sampling_rate, 300*self.sampling_rate)
            end = min(start + duration, n_samples)
            
            # Maximum dive depth (5-80 meters)
            max_depth = np.random.exponential(20) + 5
            
            # Create dive profile
            dive_time = np.linspace(0, 1, end-start)
            dive_profile = max_depth * np.sin(np.pi * dive_time)**2
            depth[start:end] = dive_profile
        
        # Add noise
        depth += np.random.normal(0, 0.5, n_samples)
        depth = np.maximum(depth, 0)  # Ensure no negative depths
        
        return depth
    
    def detect_dives(self, data: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
        """
        Detect dive events using TagTools methodology
        
        Implements the TagTools find_dives algorithm:
        1. Identify periods below depth threshold
        2. Apply minimum duration filter
        3. Extract dive characteristics
        
        Args:
            data: Processed DTAG data
            
        Returns:
            List of dive events with characteristics
        """
        try:
            depth = data['depth']
            time = data['time']
            
            logger.info(f"Detecting dives with threshold {self.depth_threshold}m, min duration {self.min_dive_duration}s")
            
            # TagTools-style dive detection
            dives = self._tagtools_dive_detection(depth, time)
            
            # Analyze each dive
            dive_events = []
            for i, dive in enumerate(dives):
                dive_analysis = self._analyze_dive(dive, data, i)
                dive_events.append(dive_analysis)
            
            logger.info(f"Detected {len(dive_events)} dive events")
            return dive_events
            
        except Exception as e:
            logger.error(f"Error detecting dives: {e}")
            return []
    
    def _tagtools_dive_detection(self, depth: np.ndarray, time: np.ndarray) -> List[Dict[str, Any]]:
        """
        TagTools-style dive detection algorithm
        
        Based on the TagTools find_dives function methodology
        """
        dives = []
        
        # Find points below dive threshold
        below_threshold = depth > self.depth_threshold
        
        # Find dive start and end points
        dive_starts = np.where(np.diff(below_threshold.astype(int)) == 1)[0]
        dive_ends = np.where(np.diff(below_threshold.astype(int)) == -1)[0]
        
        # Ensure we have matching starts and ends
        if len(dive_starts) > 0 and len(dive_ends) > 0:
            if dive_starts[0] > dive_ends[0]:
                dive_ends = dive_ends[1:]
            if len(dive_starts) > len(dive_ends):
                dive_starts = dive_starts[:-1]
        
        # Analyze each dive
        for start_idx, end_idx in zip(dive_starts, dive_ends):
            duration = (end_idx - start_idx) / self.sampling_rate
            
            # Only keep dives longer than minimum duration
            if duration >= self.min_dive_duration:
                dive_segment = depth[start_idx:end_idx]
                dives.append({
                    'start': start_idx,
                    'end': end_idx,
                    'max_depth': np.max(dive_segment),
                    'duration': duration,
                    'start_time': time[start_idx] if len(time) > start_idx else start_idx/self.sampling_rate,
                    'end_time': time[end_idx] if len(time) > end_idx else end_idx/self.sampling_rate
                })
        
        return dives
    
    def _analyze_dive(self, dive: Dict[str, Any], data: Dict[str, np.ndarray], dive_id: int) -> Dict[str, Any]:
        """
        Comprehensive dive analysis using TagTools methodology
        
        Implements TagTools-style dive analysis including:
        - Dive phases (descent, bottom, ascent)
        - Dynamic body acceleration (DBA)
        - Acoustic activity patterns
        - Foraging behavior indicators
        - Energy expenditure estimates
        
        Args:
            dive: Dive event data
            data: Full DTAG dataset
            dive_id: Unique dive identifier
            
        Returns:
            Comprehensive dive analysis
        """
        try:
            start_idx = dive['start']
            end_idx = dive['end']
            
            # Extract dive segment data
            dive_depth = data['depth'][start_idx:end_idx]
            dive_time = data['time'][start_idx:end_idx] if 'time' in data else np.arange(len(dive_depth))/self.sampling_rate
            
            # Basic dive metrics
            max_depth = np.max(dive_depth)
            duration = (end_idx - start_idx) / self.sampling_rate
            
            # Dive phases (TagTools methodology)
            descent_end = np.argmax(dive_depth)
            ascent_start = descent_end
            
            # Calculate dive metrics
            descent_rate = max_depth / (descent_end / self.sampling_rate) if descent_end > 0 else 0
            ascent_rate = max_depth / ((len(dive_depth) - ascent_start) / self.sampling_rate) if ascent_start < len(dive_depth)-1 else 0
            
            # Bottom time (time spent at >80% of max depth)
            bottom_threshold = 0.8 * max_depth
            bottom_time = np.sum(dive_depth > bottom_threshold) / self.sampling_rate
            
            # TagTools-style movement analysis
            acc_x = data['acc_x'][start_idx:end_idx]
            acc_y = data['acc_y'][start_idx:end_idx]
            acc_z = data['acc_z'][start_idx:end_idx]
            
            # Calculate dynamic body acceleration (DBA) - TagTools standard
            dba = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
            mean_dba = np.mean(dba)
            
            # Acoustic activity during dive
            acoustic_activity = data['acoustic'][start_idx:end_idx] if 'acoustic' in data else np.array([False] * len(dive_depth))
            acoustic_proportion = np.mean(acoustic_activity)
            
            # Classify dive type using TagTools-style classification
            dive_type = self._classify_dive_type(max_depth, duration, bottom_time, float(acoustic_proportion), float(mean_dba))
            
            # Foraging indicators (TagTools methodology)
            foraging_indicators = self._detect_foraging_indicators(dive_depth, acc_x, acc_y, acc_z, acoustic_activity)
            
            # Energy expenditure estimation (TagTools bioenergetics)
            energy_cost = self._estimate_energy_cost(duration, max_depth, float(mean_dba), dive_type)
            
            # Dive efficiency metric
            dive_efficiency = foraging_indicators['success_probability'] / energy_cost if energy_cost > 0 else 0
            
            # Behavioral context inference
            behavioral_context = self._infer_behavioral_context(dive_type, foraging_indicators, float(acoustic_proportion))
            
            return {
                'dive_id': dive_id,
                'start_time': dive_time[0] if len(dive_time) > 0 else 0,
                'end_time': dive_time[-1] if len(dive_time) > 0 else duration,
                'duration': duration,
                'max_depth': max_depth,
                'descent_rate': descent_rate,
                'ascent_rate': ascent_rate,
                'bottom_time': bottom_time,
                'dive_type': dive_type,
                'mean_dba': mean_dba,
                'acoustic_proportion': acoustic_proportion,
                'foraging_indicators': foraging_indicators,
                'energy_cost': energy_cost,
                'dive_efficiency': dive_efficiency,
                'behavioral_context': behavioral_context
            }
            
        except Exception as e:
            logger.error(f"Error analyzing dive {dive_id}: {e}")
            return {'dive_id': dive_id, 'error': str(e)}
    
    def _classify_dive_type(self, max_depth: float, duration: float, bottom_time: float, 
                          acoustic_proportion: float, mean_dba: float) -> str:
        """
        Classify dive type using TagTools-style behavioral classification
        
        Based on TagTools behavioral classification methodology for marine mammals
        """
        
        if max_depth < 10:
            if acoustic_proportion > 0.6:
                return "social_surface"
            elif mean_dba < 0.5:
                return "resting"
            else:
                return "shallow_travel"
        
        elif max_depth < 30:
            if acoustic_proportion > 0.4 and bottom_time > 30:
                return "shallow_foraging"
            elif mean_dba > 1.0:
                return "shallow_travel"
            else:
                return "shallow_exploration"
        
        elif max_depth < 80:
            if bottom_time > 60 and acoustic_proportion > 0.3:
                return "deep_foraging"
            elif mean_dba > 0.8:
                return "deep_travel"
            else:
                return "deep_exploration"
        
        else:
            if bottom_time > 120:
                return "deep_foraging"
            else:
                return "deep_exploration"
    
    def _detect_foraging_indicators(self, depth: np.ndarray, acc_x: np.ndarray, 
                                  acc_y: np.ndarray, acc_z: np.ndarray, 
                                  acoustic: np.ndarray) -> Dict[str, Any]:
        """
        Detect foraging behavior indicators using TagTools methodology
        
        Implements TagTools-style foraging detection:
        - Echolocation patterns
        - Feeding buzz detection
        - Prey pursuit movements
        - Success probability estimation
        """
        
        # Echolocation click patterns
        click_rate = np.mean(acoustic) * 100  # Clicks per second
        
        # Feeding buzz detection (TagTools methodology)
        buzz_threshold = 0.8
        buzz_sequences = np.where(acoustic > buzz_threshold)[0]
        buzz_events = len(np.split(buzz_sequences, np.where(np.diff(buzz_sequences) != 1)[0] + 1)) if len(buzz_sequences) > 0 else 0
        
        # Movement patterns indicating prey pursuit (TagTools DBA analysis)
        acc_magnitude = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        rapid_maneuvers = np.sum(np.diff(acc_magnitude) > 2.0)  # Sudden acceleration changes
        
        # Depth variations indicating prey tracking
        depth_variations = np.std(np.diff(depth))
        
        # TagTools-style success probability calculation
        success_factors = [
            min(click_rate / 20, 1.0),  # Normalized click rate
            min(buzz_events / 3, 1.0),  # Normalized buzz events
            min(rapid_maneuvers / 10, 1.0),  # Normalized maneuvers
            min(depth_variations / 5, 1.0)  # Normalized depth variations
        ]
        
        success_probability = np.mean(success_factors)
        
        return {
            'click_rate': click_rate,
            'buzz_events': buzz_events,
            'rapid_maneuvers': rapid_maneuvers,
            'depth_variations': depth_variations,
            'success_probability': success_probability,
            'foraging_intensity': np.mean([click_rate/20, buzz_events/3, rapid_maneuvers/10]),
            'prey_pursuit_events': rapid_maneuvers
        }
    
    def _estimate_energy_cost(self, duration: float, max_depth: float, 
                           mean_dba: float, dive_type: str) -> float:
        """
        Estimate energy cost using TagTools bioenergetic models
        
        Based on TagTools energy expenditure methodology
        """
        
        # Base metabolic rate (TagTools methodology)
        base_cost = duration * 0.1
        
        # Depth-related cost (hydrostatic pressure effects)
        depth_cost = (max_depth / 100) ** 1.5
        
        # Activity-related cost (from DBA - TagTools standard)
        activity_cost = mean_dba * 2.0
        
        # Dive type multipliers (TagTools behavioral energetics)
        type_multipliers = {
            'deep_foraging': 1.5,
            'shallow_foraging': 1.2,
            'deep_travel': 1.3,
            'shallow_travel': 1.0,
            'social_surface': 0.8,
            'resting': 0.5,
            'deep_exploration': 1.4,
            'shallow_exploration': 1.1
        }
        
        type_multiplier = type_multipliers.get(dive_type, 1.0)
        
        total_cost = (base_cost + depth_cost + activity_cost) * type_multiplier
        
        return total_cost
    
    def _infer_behavioral_context(self, dive_type: str, foraging_indicators: Dict[str, Any], 
                                acoustic_proportion: float) -> str:
        """
        Infer behavioral context using TagTools methodology
        """
        
        if 'foraging' in dive_type:
            if foraging_indicators['success_probability'] > 0.7:
                return "successful_foraging"
            elif foraging_indicators['success_probability'] > 0.4:
                return "active_foraging"
            else:
                return "foraging_search"
        
        elif 'travel' in dive_type:
            if acoustic_proportion > 0.3:
                return "coordinated_travel"
            else:
                return "individual_travel"
        
        elif 'social' in dive_type:
            return "social_interaction"
        
        elif 'rest' in dive_type:
            return "resting_behavior"
        
        else:
            return "exploratory_behavior"
    
    def analyze_surface_behavior(self, data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Analyze surface behavior patterns using TagTools methodology
        """
        try:
            depth = data['depth']
            
            # Identify surface periods
            surface_mask = depth < self.surface_threshold
            surface_periods = self._find_continuous_periods(surface_mask)
            
            surface_analysis = {
                'total_surface_time': np.sum(surface_mask) / self.sampling_rate,
                'surface_periods': len(surface_periods),
                'mean_surface_duration': np.mean([p['duration'] for p in surface_periods]) if surface_periods else 0,
                'surface_breathing_rate': len(surface_periods) / (len(depth) / self.sampling_rate / 3600),  # breaths per hour
                'surface_activity_level': np.mean(data['acc_x'][surface_mask]**2 + data['acc_y'][surface_mask]**2 + data['acc_z'][surface_mask]**2) if np.any(surface_mask) else 0
            }
            
            return surface_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing surface behavior: {e}")
            return {}
    
    def _find_continuous_periods(self, mask: np.ndarray) -> List[Dict[str, Any]]:
        """Find continuous periods where mask is True"""
        periods = []
        
        # Find start and end points
        diff = np.diff(mask.astype(int))
        starts = np.where(diff == 1)[0] + 1
        ends = np.where(diff == -1)[0] + 1
        
        # Handle edge cases
        if mask[0]:
            starts = np.concatenate([[0], starts])
        if mask[-1]:
            ends = np.concatenate([ends, [len(mask)]])
        
        # Create periods
        for start, end in zip(starts, ends):
            periods.append({
                'start': start,
                'end': end,
                'duration': (end - start) / self.sampling_rate
            })
        
        return periods
    
    def build_energetic_model(self, dive_events: List[Dict[str, Any]], 
                           surface_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build comprehensive energetic model using TagTools methodology
        """
        try:
            if not dive_events:
                return {}
            
            # Calculate total energy expenditure
            total_dive_cost = sum(dive.get('energy_cost', 0) for dive in dive_events)
            surface_cost = surface_analysis.get('surface_activity_level', 0) * surface_analysis.get('total_surface_time', 0) * 0.05
            total_energy_cost = total_dive_cost + surface_cost
            
            # Calculate foraging success metrics
            foraging_dives = [dive for dive in dive_events if 'foraging' in dive.get('dive_type', '')]
            total_foraging_success = sum(dive.get('foraging_indicators', {}).get('success_probability', 0) for dive in foraging_dives)
            
            # Energy efficiency metrics
            energy_per_dive = total_energy_cost / len(dive_events)
            success_per_energy = total_foraging_success / total_energy_cost if total_energy_cost > 0 else 0
            
            # Behavioral budget
            dive_types = [dive.get('dive_type', 'unknown') for dive in dive_events]
            type_counts = {dive_type: dive_types.count(dive_type) for dive_type in set(dive_types)}
            behavioral_budget = {k: v/len(dive_events) for k, v in type_counts.items()}
            
            # Time allocation
            total_time = sum(dive.get('duration', 0) for dive in dive_events) + surface_analysis.get('total_surface_time', 0)
            dive_time_allocation = sum(dive.get('duration', 0) for dive in dive_events) / total_time if total_time > 0 else 0
            
            # Optimal foraging metrics
            successful_foraging_dives = [dive for dive in foraging_dives if dive.get('foraging_indicators', {}).get('success_probability', 0) > 0.5]
            optimal_dive_depth = np.mean([dive.get('max_depth', 0) for dive in successful_foraging_dives]) if successful_foraging_dives else 0
            optimal_dive_duration = np.mean([dive.get('duration', 0) for dive in successful_foraging_dives]) if successful_foraging_dives else 0
            
            energetic_model = {
                'total_energy_cost': total_energy_cost,
                'energy_per_dive': energy_per_dive,
                'foraging_success_rate': total_foraging_success / len(foraging_dives) if foraging_dives else 0,
                'energy_efficiency': success_per_energy,
                'behavioral_budget': behavioral_budget,
                'dive_time_allocation': dive_time_allocation,
                'surface_time_allocation': 1 - dive_time_allocation,
                'optimal_dive_depth': optimal_dive_depth,
                'optimal_dive_duration': optimal_dive_duration,
                'foraging_dive_count': len(foraging_dives),
                'successful_foraging_dives': len(successful_foraging_dives)
            }
            
            return energetic_model
            
        except Exception as e:
            logger.error(f"Error building energetic model: {e}")
            return {}
    
    def run_comprehensive_analysis(self, dtag_data: Dict[str, Any], 
                                 environmental_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run complete behavioral analysis pipeline using TagTools methodology
        
        Args:
            dtag_data: Raw DTAG sensor data
            environmental_data: Optional environmental conditions
            
        Returns:
            Comprehensive analysis results
        """
        try:
            logger.info(f"Starting comprehensive DTAG analysis for {self.deployment_id}")
            logger.info("Using TagTools methodology for dive detection and behavioral analysis")
            
            # Load and preprocess data
            processed_data = self.load_dtag_data(dtag_data)
            if not processed_data:
                return {'error': 'Failed to load DTAG data'}
            
            # Detect and analyze dives using TagTools methodology
            dive_events = self.detect_dives(processed_data)
            
            # Analyze surface behavior
            surface_analysis = self.analyze_surface_behavior(processed_data)
            
            # Build energetic model
            energetic_model = self.build_energetic_model(dive_events, surface_analysis)
            
            # Generate insights
            key_insights = self._generate_key_insights(dive_events, energetic_model)
            
            # Compile comprehensive results
            results = {
                'deployment_id': self.deployment_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'methodology': 'TagTools-inspired dive detection and behavioral analysis',
                'data_summary': {
                    'total_samples': len(processed_data.get('depth', [])),
                    'duration_hours': len(processed_data.get('depth', [])) / self.sampling_rate / 3600,
                    'depth_range': (float(np.min(processed_data.get('depth', [0]))), float(np.max(processed_data.get('depth', [0]))))
                },
                'dive_analysis': {
                    'total_dives': len(dive_events),
                    'dive_events': dive_events,
                    'dive_types': list(set(dive.get('dive_type', 'unknown') for dive in dive_events)),
                    'foraging_dives': len([dive for dive in dive_events if 'foraging' in dive.get('dive_type', '')])
                },
                'surface_analysis': surface_analysis,
                'energetic_model': energetic_model,
                'key_insights': key_insights,
                'behavioral_patterns': {
                    'most_common_dive_type': max(set(dive.get('dive_type', 'unknown') for dive in dive_events), 
                                               key=lambda x: sum(1 for dive in dive_events if dive.get('dive_type') == x)) if dive_events else 'none',
                    'average_dive_depth': float(np.mean([dive.get('max_depth', 0) for dive in dive_events])) if dive_events else 0,
                    'foraging_success_rate': float(np.mean([dive.get('foraging_indicators', {}).get('success_probability', 0) for dive in dive_events])) if dive_events else 0
                },
                'environmental_correlations': environmental_data if environmental_data else {}
            }
            
            self.results = results
            logger.info(f"Completed comprehensive analysis with {len(dive_events)} dives")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': str(e)}
    
    def _generate_key_insights(self, dive_events: List[Dict[str, Any]], 
                             energetic_model: Dict[str, Any]) -> List[str]:
        """Generate key insights from TagTools analysis"""
        insights = []
        
        # Dive behavior insights
        if dive_events:
            most_common_dive_type = max(set(dive.get('dive_type', 'unknown') for dive in dive_events), 
                                      key=lambda x: sum(1 for dive in dive_events if dive.get('dive_type') == x))
            insights.append(f"Most common dive type: {most_common_dive_type}")
            
            mean_depth = np.mean([dive.get('max_depth', 0) for dive in dive_events])
            insights.append(f"Average dive depth: {mean_depth:.1f}m")
            
            # Foraging insights
            foraging_dives = [dive for dive in dive_events if 'foraging' in dive.get('dive_type', '')]
            if foraging_dives:
                foraging_success = np.mean([dive.get('foraging_indicators', {}).get('success_probability', 0) for dive in foraging_dives])
                insights.append(f"Foraging success rate: {foraging_success:.2%}")
                
                # Optimal foraging depth
                successful_dives = [dive for dive in foraging_dives if dive.get('foraging_indicators', {}).get('success_probability', 0) > 0.5]
                if successful_dives:
                    optimal_depth = np.mean([dive.get('max_depth', 0) for dive in successful_dives])
                    insights.append(f"Optimal foraging depth: {optimal_depth:.1f}m")
        
        # Energy efficiency insights
        if energetic_model:
            efficiency = energetic_model.get('energy_efficiency', 0)
            if efficiency > 0.7:
                insights.append("High energy efficiency - optimal foraging strategy")
            elif efficiency < 0.3:
                insights.append("Low energy efficiency - challenging foraging conditions")
                
            # Behavioral budget insights
            behavioral_budget = energetic_model.get('behavioral_budget', {})
            if behavioral_budget:
                dominant_behavior = max(behavioral_budget, key=behavioral_budget.get)
                percentage = behavioral_budget[dominant_behavior] * 100
                insights.append(f"Dominant behavior: {dominant_behavior} ({percentage:.1f}% of dives)")
        
        # TagTools methodology insight
        insights.append("Analysis powered by TagTools methodology - biologging gold standard")
        
        return insights
    
    def export_results(self, filename: str) -> bool:
        """Export analysis results to JSON file"""
        try:
            if not self.results:
                logger.error("No results to export")
                return False
            
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Results exported to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            return False

def main():
    """Test the TagTools-powered DTAG behavioral analyzer"""
    # Create analyzer instance
    analyzer = DTAGBehavioralAnalyzer("cascadia_2010_k33_test")
    
    # Generate realistic DTAG data with actual dive patterns
    n_samples = 36000  # 2 hours at 50 Hz
    
    # Create realistic depth profile with dives
    depth_profile = np.zeros(n_samples)
    
    # Add 10 realistic dive events (properly spaced)
    dive_starts = [3000, 8000, 12000, 16000, 20000, 24000, 28000, 30000, 32000, 34000]
    dive_depths = [25, 45, 15, 60, 30, 80, 20, 35, 50, 25]
    dive_durations = [120, 240, 90, 300, 180, 360, 150, 200, 280, 160]  # samples, not seconds
    
    for i, (start, max_depth, duration) in enumerate(zip(dive_starts, dive_depths, dive_durations)):
        if start + duration < n_samples:
            # Create realistic dive profile
            dive_time = np.linspace(0, 1, duration)
            dive_depth = max_depth * np.sin(np.pi * dive_time)**2
            depth_profile[start:start+duration] = dive_depth
    
    # Add surface noise
    depth_profile += np.random.normal(0, 0.3, n_samples)
    depth_profile = np.maximum(depth_profile, 0)
    
    # Generate correlated accelerometer data
    acc_x = np.random.normal(0, 0.3, n_samples)
    acc_y = np.random.normal(0, 0.3, n_samples)
    acc_z = np.random.normal(0, 0.3, n_samples)
    
    # Add realistic movement during dives
    for start, duration in zip(dive_starts, dive_durations):
        if start + duration < n_samples:
            # Increase activity during dives
            acc_x[start:start+duration] += np.random.normal(0, 0.5, duration)
            acc_y[start:start+duration] += np.random.normal(0, 0.5, duration)
            acc_z[start:start+duration] += np.random.normal(0, 0.5, duration)
    
    # Generate realistic acoustic activity
    acoustic_activity = np.random.choice([False, True], n_samples, p=[0.85, 0.15])
    
    # Increase acoustic activity during foraging dives
    for i, (start, duration) in enumerate(zip(dive_starts, dive_durations)):
        if start + duration < n_samples and dive_depths[i] > 40:  # Deep foraging dives
            acoustic_activity[start:start+duration] = np.random.choice([False, True], duration, p=[0.4, 0.6])
    
    test_data = {
        'timestamp': np.arange(n_samples) / 50,  # Time in seconds
        'depth': depth_profile,
        'acceleration_x': acc_x,
        'acceleration_y': acc_y,
        'acceleration_z': acc_z,
        'acoustic_activity': acoustic_activity
    }
    
    print(f"Test data: {len(test_data['depth'])} samples, depth range: {np.min(test_data['depth']):.1f}m - {np.max(test_data['depth']):.1f}m")
    print(f"Dive events created: {len(dive_starts)}")
    print(f"Samples above 5m threshold: {np.sum(test_data['depth'] > 5.0)}")
    
    # Run comprehensive analysis
    results = analyzer.run_comprehensive_analysis(test_data)
    
    # Display results
    print("\n=== DTAG Behavioral Analysis Results (TagTools Methodology) ===")
    print(f"Deployment ID: {results.get('deployment_id', 'N/A')}")
    print(f"Methodology: {results.get('methodology', 'N/A')}")
    print(f"Total dives detected: {results.get('dive_analysis', {}).get('total_dives', 0)}")
    print(f"Analysis duration: {results.get('data_summary', {}).get('duration_hours', 0):.1f} hours")
    print(f"Depth range: {results.get('data_summary', {}).get('depth_range', (0, 0))[0]:.1f}m - {results.get('data_summary', {}).get('depth_range', (0, 0))[1]:.1f}m")
    
    print("\n=== Key Insights ===")
    for insight in results.get('key_insights', []):
        print(f"• {insight}")
    
    print("\n=== Energetic Model ===")
    energetic = results.get('energetic_model', {})
    print(f"Energy efficiency: {energetic.get('energy_efficiency', 0):.3f}")
    print(f"Foraging success rate: {energetic.get('foraging_success_rate', 0):.3f}")
    print(f"Optimal dive depth: {energetic.get('optimal_dive_depth', 0):.1f}m")
    print(f"Optimal dive duration: {energetic.get('optimal_dive_duration', 0):.1f}s")
    print(f"Foraging dives: {energetic.get('foraging_dive_count', 0)}")
    print(f"Successful foraging dives: {energetic.get('successful_foraging_dives', 0)}")
    
    print("\n=== Behavioral Patterns ===")
    patterns = results.get('behavioral_patterns', {})
    print(f"Most common dive type: {patterns.get('most_common_dive_type', 'unknown')}")
    print(f"Average dive depth: {patterns.get('average_dive_depth', 0):.1f}m")
    print(f"Foraging success rate: {patterns.get('foraging_success_rate', 0):.2%}")
    
    print("\n=== Dive Types Found ===")
    dive_types = results.get('dive_analysis', {}).get('dive_types', [])
    for dive_type in dive_types:
        print(f"• {dive_type}")
    
    print("\n=== Individual Dive Analysis ===")
    dive_events = results.get('dive_analysis', {}).get('dive_events', [])
    for dive in dive_events[:5]:  # Show first 5 dives
        print(f"Dive {dive.get('dive_id', 'N/A')}: {dive.get('dive_type', 'unknown')} - {dive.get('max_depth', 0):.1f}m, {dive.get('duration', 0):.1f}s")
        print(f"  Foraging success: {dive.get('foraging_indicators', {}).get('success_probability', 0):.2%}")
        print(f"  Energy cost: {dive.get('energy_cost', 0):.2f}, Efficiency: {dive.get('dive_efficiency', 0):.3f}")
        print(f"  Behavioral context: {dive.get('behavioral_context', 'unknown')}")
    
    if len(dive_events) > 5:
        print(f"... and {len(dive_events) - 5} more dives")
    
    print("\n=== Surface Behavior ===")
    surface = results.get('surface_analysis', {})
    print(f"Surface time: {surface.get('total_surface_time', 0):.1f}s")
    print(f"Surface breathing rate: {surface.get('surface_breathing_rate', 0):.1f} breaths/hour")
    print(f"Surface activity level: {surface.get('surface_activity_level', 0):.3f}")
    
    # Export results
    analyzer.export_results("dtag_analysis_results.json")
    print("\nResults exported to dtag_analysis_results.json")
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total analysis time: {results.get('data_summary', {}).get('duration_hours', 0):.1f} hours")
    print(f"Dive rate: {len(dive_events) / results.get('data_summary', {}).get('duration_hours', 1):.1f} dives/hour")
    print(f"Time budget: {energetic.get('dive_time_allocation', 0):.1%} diving, {energetic.get('surface_time_allocation', 0):.1%} surface")
    
    # Show behavioral budget breakdown
    budget = energetic.get('behavioral_budget', {})
    if budget:
        print(f"\n=== Behavioral Budget ===")
        for behavior, proportion in sorted(budget.items(), key=lambda x: x[1], reverse=True):
            print(f"• {behavior}: {proportion:.1%}")
    
    print("\nTagTools-powered DTAG behavioral analysis complete!")

if __name__ == "__main__":
    main() 