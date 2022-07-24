from datetime import date
from flask import request
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, SearchField, SubmitField
from wtforms.validators import DataRequired, Optional


class SearchForm(FlaskForm):
    q = SearchField('Search Anime', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)


class TrackerForm(FlaskForm):
    def max_episodes(self):
        return self.anime.total_episodes
    
    watched_episodes = IntegerField('Episodes Watched', default=0, validators=[Optional()])
    start_date = DateField('Start Date', default=date.today, validators=[Optional()])
    end_date = DateField('End Date', default=date.today, validators=[Optional()])
    status = SelectField('Status', choices=['Watching', 'Completed', 'Holding', 'Dropped', 'Planning'])
    submit = SubmitField('Submit')

    def __init__(self, anime, *args, **kwargs):
        super(TrackerForm, self).__init__(*args, **kwargs)
        self.anime = anime


class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')