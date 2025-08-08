from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key
    """
    return dictionary.get(key)


@register.filter
def average(values):
    """
    Calculate the average of a list of values
    """
    if not values:
        return 0
    return sum(values) / len(values)


@register.filter
def color_to_rgb(hex_color):
    """
    Convert hex color to RGB format
    """
    # Remove # if present
    hex_color = hex_color.replace('#', '')
    
    # Convert 3-digit hex to 6-digits
    if len(hex_color) == 3:
        hex_color = hex_color[0] + hex_color[0] + hex_color[1] + hex_color[1] + hex_color[2] + hex_color[2]
    
    # Convert hex to rgb
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
    except ValueError:
        return "0, 0, 0"


@register.filter
def calculate_progress(current_value, target_value):
    """
    Calculate progress percentage for goals
    """
    if not current_value or not target_value:
        return 0
    
    current_value = float(current_value)
    target_value = float(target_value)
    
    # For weight, blood pressure, cholesterol (lower is better)
    if current_value > target_value:
        # Calculate how much progress has been made
        # If current is higher than target, progress is less than 100%
        # The further current is from target, the lower the progress
        # We'll use a formula that gives diminishing returns
        difference = current_value - target_value
        max_difference = target_value  # Assume max is double the target
        
        if difference >= max_difference:
            return 0  # No progress if current is double or more of target
        
        progress = 100 * (1 - (difference / max_difference))
        return int(max(0, min(100, progress)))
    else:
        # Already reached or exceeded goal
        return 100


@register.filter
def default_if_none(value, default):
    """
    Return default if value is None
    """
    if value is None:
        return default
    return value