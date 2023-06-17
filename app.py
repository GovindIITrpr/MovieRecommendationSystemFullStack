from flask import Flask, render_template, request
import pandas as pd
import pickle
import requests
import time
app = Flask(__name__)
timestamp = int(time.time())

def fetch_poster(movie_id):
    response = requests.get(
        'https://api.themoviedb.org/3/movie/{}?api_key=6f7398664c3464c1e3457877381c51fc&language=en-US'.format(movie_id)
    )
    data = response.json()
    poster_path = data.get('poster_path')
    if poster_path:
        return "https://image.tmdb.org/t/p/w300/" + poster_path  # Adjust the size as desired
    else:
        return None


def get_movie_details(movie):
    movie_details = movies[movies['title'] == movie]
    if not movie_details.empty:
        movie_id = movie_details.iloc[0]['movie_id']
        poster = fetch_poster(movie_id)
        response = requests.get(
            'https://api.themoviedb.org/3/movie/{}/credits?api_key=6f7398664c3464c1e3457877381c51fc'.format(movie_id)
        )
        credits = response.json()
        cast = [actor['name'] for actor in credits.get('cast', [])[:5]]  # Get first 5 cast members
        overview = movie_details.iloc[0].get('overview', '')  # Check if 'overview' key exists, set to empty string if not
        return movie_id, poster, overview, cast
    return None, None, None, None

def recommend(movie):
    movie_id, poster, overview, cast = get_movie_details(movie)
    if movie_id and poster:
        recommended_movies = []
        recommended_movies_posters = []
        movie_idx = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_idx]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])
        for i in movies_list[1:10]:
            recommended_movie_id = movies.iloc[i[0]].movie_id
            recommended_movies.append((movies.iloc[i[0]].title))
            recommended_movies_posters.append(fetch_poster(recommended_movie_id))
        return movie_id, poster, overview, cast, recommended_movies, recommended_movies_posters
    return None, None, None, None, None, None


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        selected_movie_name = request.form['movie_name']
        print(selected_movie_name);
        movie_id, poster, overview, cast, recommended_movies, recommended_movies_posters = recommend(selected_movie_name)
        return render_template('index.html', movie_id=movie_id, poster=poster, overview=overview, cast=cast,
                               recommended_movie_names=recommended_movies,
                               recommended_movie_posters=recommended_movies_posters, timestamp=timestamp)
    else:
        response = requests.get('https://api.themoviedb.org/3/movie/popular?api_key=6f7398664c3464c1e3457877381c51fc&language=en-US')
        data = response.json()
        movie_names = [movie['title'] for movie in data.get('results', [])]
        return render_template('index.html', movie_names=movie_names, timestamp=timestamp)

 
if __name__ == '__main__':
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    app.run(debug=True)