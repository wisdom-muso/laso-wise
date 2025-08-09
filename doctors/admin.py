from django.contrib import admin
from .models import (
    Education,
    Experience,
    TimeRange,
    Saturday,
    Sunday,
    Monday,
    Wednesday,
    Thursday,
    Friday,
)

class TimeRangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time', 'duration')
    list_filter = ('start', 'end')
    search_fields = ('start', 'end')
    
    def start_time(self, obj):
        return obj.start.strftime('%I:%M %p')
    
    def end_time(self, obj):
        return obj.end.strftime('%I:%M %p')
    
    def duration(self, obj):
        # Calculate duration in hours and minutes
        start_minutes = obj.start.hour * 60 + obj.start.minute
        end_minutes = obj.end.hour * 60 + obj.end.minute
        
        # Handle cases where end time is on the next day
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
            
        duration_minutes = end_minutes - start_minutes
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        
        return f"{hours}h {minutes}m"
    
    duration.short_description = "Duration"
    start_time.short_description = "Start Time"
    end_time.short_description = "End Time"

class DayScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_time_ranges')
    filter_horizontal = ('time_range',)
    
    def display_time_ranges(self, obj):
        return ", ".join([f"{t.start.strftime('%I:%M %p')} - {t.end.strftime('%I:%M %p')}" for t in obj.time_range.all()])
    
    display_time_ranges.short_description = "Time Ranges"

class EducationAdmin(admin.ModelAdmin):
    list_display = ('user', 'degree', 'college', 'year_of_completion')
    list_filter = ('year_of_completion',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'degree', 'college')

class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'designation', 'institution', 'from_year', 'to_year')
    list_filter = ('from_year', 'to_year')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'designation', 'institution')

admin.site.register(Education, EducationAdmin)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(TimeRange, TimeRangeAdmin)
admin.site.register(Saturday, DayScheduleAdmin)
admin.site.register(Sunday, DayScheduleAdmin)
admin.site.register(Monday, DayScheduleAdmin)
admin.site.register(Wednesday, DayScheduleAdmin)
admin.site.register(Thursday, DayScheduleAdmin)
admin.site.register(Friday, DayScheduleAdmin)
