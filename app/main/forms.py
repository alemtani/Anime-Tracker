from datetime import date
from flask import request
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError


class SearchForm(FlaskForm):
    q = StringField('Search Anime', validators=[DataRequired()])
    submit = SubmitField('Search')

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)


class TrackerForm(FlaskForm):
    def max_episodes(self):
        return self.anime.total_episodes
    
    watched_episodes = IntegerField('Episodes Watched', default=0)
    start_date = DateField('Start Date', default=date.today)
    end_date = DateField('End Date', default=date.today)
    status = SelectField('Status', choices=['Watching', 'Completed', 'Holding', 'Dropped', 'Planning'])
    submit = SubmitField('Submit')

    def __init__(self, anime, *args, **kwargs):
        super(TrackerForm, self).__init__(*args, **kwargs)
        self.anime = anime

    def validate_watched_episodes(self, watched_episodes):
        if watched_episodes.data is not None:
            if watched_episodes.data < 0:
                raise ValidationError('Watched episodes cannot be negative.')
            elif self.anime.total_episodes != 0 and watched_episodes.data > self.anime.total_episodes:
                raise ValidationError(f'Watched episodes cannot exceed {self.anime.total_episodes} episodes.')


class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')