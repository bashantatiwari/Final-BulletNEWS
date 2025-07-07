from django.contrib import admin
from .models import MCQQuestion, MCQOption, MCQResponse

class MCQOptionInline(admin.TabularInline):
    model = MCQOption
    extra = 4
    max_num = 4

@admin.register(MCQQuestion)
class MCQQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question_text',)
    inlines = [MCQOptionInline]

@admin.register(MCQResponse)
class MCQResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected_option', 'is_correct', 'submitted_at', 'wants_another')
    list_filter = ('is_correct', 'submitted_at', 'wants_another')
    search_fields = ('user__username', 'question__question_text')
    readonly_fields = ('submitted_at',)
