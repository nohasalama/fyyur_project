#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False) 
    seeking_description = db.Column(db.String(120))

    shows = db.relationship('Show', backref='venue')

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))

    shows = db.relationship('Show', backref='artist')

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)

    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # num_shows should be aggregated based on number of upcoming shows per venue.  
  query_venues = Venue.query.order_by(Venue.city,Venue.state).all()

  data = []
  current_data = {} #one item (same city & state) of the list that will be appended to data
  venues = [] #the list of venues belonging to one item of the list
  city = query_venues[0].city 
  state = query_venues[0].state

  for venue in query_venues:
    if venue.city != city and venue.state !=state: #check if we have a new combination of (city and state)
      current_data['city'] = city
      current_data['state'] = state
      current_data['venues'] = venues
      data.append(current_data)

      #clear variables for next iteration
      city = venue.city
      state = venue.state
      current_data = {}
      venues = []

    num_upcoming_shows = len(list(filter(lambda show: show.start_time >= datetime.now(),
                                                  venue.shows)))

    current_venue = {
    "id" : venue.id,
    "name" : venue.name,
    "num_upcoming_shows" : num_upcoming_shows
    }
    venues.append(current_venue)

  #for the last iteration
  current_data['city'] = city 
  current_data['state'] = state
  current_data['venues'] = venues
  data.append(current_data)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '') #get partial string from form
  search_like = "%{}%".format(search_term)
  query_venues = Venue.query.filter(Venue.name.ilike(search_like)).all() #get all venues with the given partial string returned in the form

  response = {} 
  response['count'] = len(query_venues)

  data = []
  for venue in query_venues:
    current_data = {
    "id": venue.id,
    "name": venue.name,
    "num_upcoming_shows": len(list(filter(lambda show: show.start_time >= datetime.now(),
                                                  venue.shows)))
    }
    data.append(current_data)
  response['data'] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.get(venue_id) #get venue data with the given venue_id
  data = {}

  data['id'] = venue.id
  data['name'] = venue.name
  data['address'] = venue.address
  data['city'] = venue.city
  data['state'] = venue.state
  data['phone'] = venue.phone
  data['facebook_link'] = venue.facebook_link
  data['image_link'] = venue.image_link
  data['website'] = venue.website
  data['seeking_talent'] = venue.seeking_talent
  data['seeking_description'] = venue.seeking_description

  if venue.genres == None:
    data['genres'] = ""
  else:
    data['genres'] = venue.genres.split(',')
    
  past_shows_all = list(filter(lambda show: show.start_time < datetime.now(),
                                                  venue.shows))
  upcoming_shows_all = list(filter(lambda show: show.start_time >= datetime.now(),
                                                  venue.shows))

  past_shows = []
  for past_show in past_shows_all:
    past_shows.append({
      'artist_id': past_show.artist_id,
      'artist_name': past_show.artist.name,
      'artist_image_link': past_show.artist.image_link,
      'start_time': past_show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })
  data['past_shows'] = past_shows

  upcoming_shows = []
  for upcoming_show in upcoming_shows_all:
    upcoming_shows.append({
      'artist_id': upcoming_show.artist_id,
      'artist_name': upcoming_show.artist.name,
      'artist_image_link': upcoming_show.artist.image_link,
      'start_time': upcoming_show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })
  data['upcoming_shows'] = upcoming_shows

  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try: 
    venue = Venue()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']

    split_comma = ","
    venue.genres = split_comma.join(request.form.getlist('genres'))

    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try: 
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    # on successful db insert, flash success
    flash('Venue was successfully deleted!')
  else:
    flash('An error occurred. Venue could not be deleted.')

  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  search_like = "%{}%".format(search_term)
  query_artists = Artist.query.filter(Artist.name.ilike(search_like)).all() #serach all artists with the given partial string returned in the form

  response = {}
  response['count'] = len(query_artists)

  data = []
  for artist in query_artists:
    current_data = {
    "id": artist.id,
    "name": artist.name,
    "num_upcoming_shows": len(list(filter(lambda show: show.start_time >= datetime.now(),
                                                  artist.shows)))
    }
    data.append(current_data)
  response['data'] = data

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  artist = Artist.query.get(artist_id)
  data = {}

  data['id'] = artist.id
  data['name'] = artist.name
  data['city'] = artist.city
  data['state'] = artist.state
  data['phone'] = artist.phone
  data['website'] = artist.website
  data['facebook_link'] = artist.facebook_link
  data['seeking_venue'] = artist.seeking_venue
  data['seeking_description'] = artist.seeking_description
  data['image_link'] = artist.image_link

  if artist.genres == None:
    data['genres'] = ""
  else:
    data['genres'] = artist.genres.split(',')
    
  past_shows_all = list(filter(lambda show: show.start_time < datetime.now(),
                                                  artist.shows))
  upcoming_shows_all = list(filter(lambda show: show.start_time >= datetime.now(),
                                                  artist.shows))

  past_shows = []
  for past_show in past_shows_all:
    past_shows.append({
      'venue_id': past_show.venue_id,
      'venue_name': past_show.venue.name,
      'venue_image_link': past_show.venue.image_link,
      'start_time': past_show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })
  data['past_shows'] = past_shows

  upcoming_shows = []
  for upcoming_show in upcoming_shows_all:
    upcoming_shows.append({
      'venue_id': upcoming_show.venue_id,
      'venue_name': upcoming_show.venue.name,
      'venue_image_link': upcoming_show.venue.image_link,
      'start_time': upcoming_show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })
  data['upcoming_shows'] = upcoming_shows

  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)

  if artist.genres == None:
    genres = ""
  else:
    genres = artist.genres.split(',')

  form = ArtistForm(name=artist.name, genres=genres, city=artist.city, state=artist.state, phone=artist.phone, website=artist.website, facebook_link= artist.facebook_link, seeking_venue=artist.seeking_venue, seeking_description=artist.seeking_description, image_link=artist.image_link)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  error = False

  try: 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']

    split_comma = ","
    artist.genres = split_comma.join(request.form.getlist('genres'))

    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  else:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)

  if venue.genres == None:
    genres = ""
  else:
    genres = venue.genres.split(',')

  form = VenueForm(name=venue.name, genres=genres, address=venue.address, city=venue.city, state=venue.state, phone=venue.phone, website=venue.website, facebook_link= venue.facebook_link, seeking_talent=venue.seeking_talent, seeking_description=venue.seeking_description, image_link=venue.image_link)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  error = False

  try: 
    venue.name = request.form['name']
    venue.address = request.form['address']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']

    split_comma = ","
    venue.genres = split_comma.join(request.form.getlist('genres'))

    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  else:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  try: 
    artist = Artist()
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']

    split_comma = ","
    artist.genres = split_comma.join(request.form.getlist('genres'))

    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  query_shows = Show.query.all()

  data = []
  for show in query_shows:
    current_data = {
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "artist_id": show.artist_id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    data.append(current_data)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  try: 
    show = Show()
    show.artist_id = request.form['artist_id']
    show.venue_id = request.form['venue_id']
    show.start_time = request.form['start_time']

    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed.')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')
    
#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
