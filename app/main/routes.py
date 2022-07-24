import requests

from app import db
from app.main import bp
from app.main.forms import DeleteForm, SearchForm, TrackerForm
from app.models import Anime, Tracker
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from urllib.parse import parse_qs, urlparse


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    '''Returns a list of animes that the current user is tracking in most recent order.
    Also allows for editing and deleting animes tracked, as well as quick 
    functionality for incrementing the number of episodes watched.'''
    delete_form = DeleteForm()
    search_form = SearchForm()
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', type=str)
    trackers = current_user.trackers
    if status is not None and status != '':
        # Filter the list of trackers by status
        trackers = trackers.filter_by(status=status)
        if trackers.first() is None:
            # Check if there is a tracker
            flash(f'No tracker found with the status: {status}')
            return redirect(url_for('main.index', page=page))
    # Order by most recent (by end date and then by start date)
    trackers = trackers.order_by(Tracker.end_date.desc(), 
        Tracker.start_date.desc()).paginate(page, current_app.config['TRACKERS_PER_PAGE'], False)
    next_url = url_for('main.index', page=trackers.next_num, status=status) if trackers.has_next else None
    prev_url = url_for('main.index', page=trackers.prev_num, status=status) if trackers.has_prev else None
    return render_template('index.html', title='Home', delete_form=delete_form, 
        search_form=search_form, trackers=trackers.items, 
        status=status, next_url=next_url, prev_url=prev_url)


@bp.route('/search')
@login_required
def search():
    '''Returns the results of searching via using MyAnimeList API. Also grants access for
    tracking watch progress for the anime.'''
    def get_api_request(q, offset):
        payload = {'q': q, 'offset': offset}
        base_url = current_app.config['MAL_BASE_URL']
        response = requests.get(base_url, params=payload, headers=current_app.config['MAL_HEADERS'])
        if response.status_code == 200:
            response = response.json()
            data = {'animes': [], 'paging': response['paging']}
            for anime in response['data']:
                id = anime['node']['id']
                fields = {'fields': 'num_episodes'}
                details = requests.get(f'{base_url}/{id}', params=fields, 
                    headers=current_app.config['MAL_HEADERS'])
                if details.status_code == 200:
                    details = details.json()
                    if details is not None and details.get('title') is not None:
                        detail = {
                            'title': details['title'],
                            'image_url': details['main_picture'].get('medium') 
                                if details.get('main_picture') else '',
                            'total_episodes': details['num_episodes'] 
                                if details.get('num_episodes') else 0
                        }
                        data['animes'].append(detail)
            return data
        else:
            return None
    
    def get_offset(url):
        parsed_url = urlparse(url)
        try:
            offset = parse_qs(parsed_url.query)['offset'][0]
        except:
            offset = None
        finally:
            return offset

    q = request.args.get('q', '', type=str)
    if q is None or q == '':
        flash('No search query entered!')
        return redirect(url_for('main.index'))
    offset = request.args.get('offset', 0, type=int)
    data = get_api_request(q, offset)
    if data is None:
        flash(f'Could not find anime with search query: {q}')
        return redirect(url_for('main.index'))
    animes = []
    for anime_data in data['animes']:
        # Get anime from db or create new one to store
        anime = Anime.query.filter_by(title=anime_data['title']).first()
        if anime is None:
            anime = Anime(title=anime_data['title'][:100], 
                image_url=anime_data['image_url'], total_episodes=anime_data['total_episodes'])
            db.session.add(anime)
            db.session.commit()
            anime = Anime.query.filter_by(title=anime.title).first()
        animes.append(anime)
    next_offset = get_offset(data['paging']['next']) if data['paging'].get('next') is not None else None
    prev_offset = get_offset(data['paging']['previous']) if data['paging'].get('previous') is not None else None
    return render_template('search.html', title='Search', animes=animes, q=q, 
        next_offset=next_offset, prev_offset=prev_offset)


@bp.route('/<anime_id>/track', methods=['GET', 'POST'])
@login_required
def track(anime_id):
    '''Returns a form to create a progress tracker for an anime if the anime has not been
    tracked yet. Otherwise return to the home page as it has already been tracked.
    Upon submit, handles the logic for adding the progress tracker to the database.'''
    anime = Anime.query.filter_by(id=anime_id).first_or_404()
    found_tracker = Tracker.query.filter_by(user=current_user, anime=anime).first()
    if found_tracker is not None:
        flash(f'You are already tracking { anime.title }.')
        return redirect(url_for('main.index'))
    tracker_form = TrackerForm(anime)
    if tracker_form.validate_on_submit():
        if tracker_form.watched_episodes.data < 0:
            flash('Watched episodes cannot be negative.')
            return redirect(url_for('main.track', anime_id=anime_id))
        if tracker_form.watched_episodes.data > anime.total_episodes:
            flash(f'Watched episodes cannot exceed {anime.total_episodes}.')
            return redirect(url_for('main.track', anime_id=anime_id))
        if tracker_form.start_date.data > tracker_form.end_date.data:
            flash('Start date cannot be pased end date.')
            return redirect(url_for('main.track', anime_id=anime_id))
        tracker = Tracker(user=current_user, anime=anime, 
            watched_episodes=tracker_form.watched_episodes.data, 
            start_date=tracker_form.start_date.data, end_date=tracker_form.end_date.data, 
            status=tracker_form.status.data)
        db.session.add(tracker)
        db.session.commit()
        flash(f'You tracked your progress for { anime.title }!')
        return redirect(url_for('main.index'))
    total_episodes = anime.total_episodes if anime.total_episodes > 0 else '?'
    return render_template('tracker_form.html', title='Track', anime=anime, 
        tracker_form=tracker_form, total_episodes=total_episodes)


@bp.route('/tracker/<tracker_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tracker(tracker_id):
    '''Returns a form to edit progress for an anime. Also allows for deleting tracking
    progress for the anime within the form. Upon submit, handles the logic for editing
    the progress tracker in the database.'''
    tracker = Tracker.query.filter_by(id=tracker_id).first_or_404()
    tracker_form = TrackerForm(tracker.anime)
    if tracker_form.validate_on_submit():
        if tracker_form.watched_episodes.data < 0:
            flash('Watched episodes cannot be negative.')
            return redirect(url_for('main.edit_tracker', tracker_id=tracker_id))
        if tracker_form.watched_episodes.data > tracker.anime.total_episodes:
            flash(f'Watched episodes cannot exceed {tracker.anime.total_episodes}.')
            return redirect(url_for('main.edit_tracker', tracker_id=tracker_id))
        if tracker_form.start_date.data > tracker_form.end_date.data:
            flash('Start date cannot be pased end date.')
            return redirect(url_for('main.edit_tracker', tracker_id=tracker_id))
        tracker.watched_episodes = tracker_form.watched_episodes.data
        tracker.start_date = tracker_form.start_date.data
        tracker.end_date = tracker_form.end_date.data
        tracker.status = tracker_form.status.data
        db.session.commit()
        flash(f'You updated your progress for { tracker.anime.title }!')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        tracker_form.watched_episodes.data = tracker.watched_episodes
        tracker_form.start_date.data = tracker.start_date
        tracker_form.end_date.data = tracker.end_date
        tracker_form.status.data = tracker.status
    delete_form = DeleteForm()
    total_episodes = tracker.anime.total_episodes if tracker.anime.total_episodes > 0 else '?'
    return render_template('tracker_form.html', title='Edit', tracker_id=tracker.id, anime=tracker.anime, 
        tracker_form=tracker_form, delete_form=delete_form, total_episodes=total_episodes)


@bp.route('/tracker/<tracker_id>/delete', methods=['POST'])
def delete_tracker(tracker_id):
    '''Deletes a progress tracker for an anime.'''
    tracker = Tracker.query.filter_by(id=tracker_id).first_or_404()
    title = tracker.anime.title
    db.session.delete(tracker)
    db.session.commit()
    flash(f'Successfully deleted tracker for {title}!')
    return redirect(url_for('main.index'))