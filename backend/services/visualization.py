# backend/services/visualization.py - COMPLETE VISUALIZATION SERVICE
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend

import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class VisualizationService:
    def __init__(self):
        # Set matplotlib to non-interactive mode
        plt.ioff()
    
    def generate_wordcloud_data(self, texts):
        """Generate wordcloud and return as base64 string"""
        try:
            if not texts or len(texts) == 0:
                return None
                
            # Combine all texts
            combined_text = " ".join(texts)
            
            if not combined_text.strip():
                return None
            
            # Generate wordcloud
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                max_words=100,
                colormap='viridis'
            ).generate(combined_text)
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            buffer.seek(0)
            
            # Encode to base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            plt.close(fig)  # Important: Close figure to free memory
            buffer.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate wordcloud: {e}")
            return None
    
    def generate_sentiment_pie_chart(self, counts):
        """Generate sentiment pie chart and return as base64 string"""
        try:
            if not counts or sum(counts.values()) == 0:
                return None
            
            labels = ['Positive', 'Negative', 'Neutral']
            sizes = [counts.get('positive', 0), counts.get('negative', 0), counts.get('neutral', 0)]
            colors = ['#10B981', '#EF4444', '#F59E0B']
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 8))
            wedges, texts, autotexts = ax.pie(
                sizes, 
                labels=labels, 
                colors=colors, 
                autopct='%1.1f%%',
                startangle=90
            )
            
            ax.set_title('', fontsize=16, pad=20)
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            buffer.seek(0)
            
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            plt.close(fig)
            buffer.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate pie chart: {e}")
            return None
    
    def generate_sentiment_bar_chart(self, counts):
        """Generate sentiment bar chart and return as base64 string"""
        try:
            if not counts or sum(counts.values()) == 0:
                return None
            
            sentiments = ['Positive', 'Negative', 'Neutral']
            values = [counts.get('positive', 0), counts.get('negative', 0), counts.get('neutral', 0)]
            colors = ['#10B981', '#EF4444', '#F59E0B']
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(sentiments, values, color=colors, alpha=0.8)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{int(value)}', ha='center', va='bottom', fontsize=12)
            
            ax.set_title('Sentiment Analysis Results', fontsize=16, pad=20)
            ax.set_ylabel('Number of Comments', fontsize=12)
            ax.grid(axis='y', alpha=0.3)
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            buffer.seek(0)
            
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            plt.close(fig)
            buffer.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate bar chart: {e}")
            return None
