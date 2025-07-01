import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class VisualizationService:
    """Service for generating progress visualization charts"""
    
    @staticmethod
    def generate_progress_chart(stats: dict) -> str:
        """
        Generate a progress visualization chart
        
        Args:
            stats: Dictionary containing user statistics:
                - workouts_completed: Total completed workouts
                - weekly_completion_rate: Weekly workout completion rate
                - exercise_completion_rate: Exercise completion rate
                - diet_adherence: Diet plan adherence rate
                - weekly_trend: List of workout counts for last 7 days
        
        Returns:
            str: Base64 encoded image URL of the generated chart
        """
        try:
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
            fig.suptitle(f"Fitness Progress Report\nTotal Workouts: {stats['workouts_completed']}", 
                        fontsize=16, y=0.95)
            
            # Plot 1: Progress Metrics
            metrics = {
                'Weekly Completion': stats['weekly_completion_rate'],
                'Exercise Completion': stats['exercise_completion_rate'],
                'Diet Adherence': stats['diet_adherence']
            }
            
            bars = ax1.bar(metrics.keys(), metrics.values(), color=['#2ecc71', '#3498db', '#e74c3c'])
            ax1.set_ylim(0, 100)
            ax1.set_ylabel('Completion Rate (%)')
            ax1.set_title('Progress Metrics', pad=20)
            
            # Add percentage labels on bars
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%',
                        ha='center', va='bottom')
            
            # Plot 2: Weekly Trend
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ax2.plot(days, stats['weekly_trend'], marker='o', linestyle='-', color='#3498db')
            ax2.set_ylim(bottom=0)
            ax2.set_ylabel('Workouts Completed')
            ax2.set_title('Weekly Workout Trend', pad=20)
            
            # Add value labels on points
            for i, v in enumerate(stats['weekly_trend']):
                ax2.text(i, v, str(v), ha='center', va='bottom')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            
            # Convert to base64
            img_str = base64.b64encode(buf.read()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generating progress chart: {e}")
            return None 