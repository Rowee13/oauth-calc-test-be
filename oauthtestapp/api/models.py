from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Conversion(models.Model):
    """
    Model to store meter-to-feet conversion history
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='conversions',
        help_text="User who performed the conversion"
    )
    meters_value = models.DecimalField(
        max_digits=10, 
        decimal_places=6,
        help_text="Input value in meters"
    )
    feet_value = models.DecimalField(
        max_digits=10, 
        decimal_places=6,
        help_text="Converted value in feet"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the conversion was performed"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the user (optional)"
    )
    
    class Meta:
        ordering = ['-timestamp']  # Most recent first
        verbose_name = "Conversion"
        verbose_name_plural = "Conversions"
    
    def __str__(self):
        return f"{self.user.username}: {self.meters_value}m → {self.feet_value}ft"
    
    @property
    def conversion_formula_used(self):
        """Return the conversion formula for reference"""
        return "feet = meters × 3.28084"
