from apikeys import TMDB_KEY
import json
import requests
from datetime import datetime
from bokeh.charts import Line,TimeSeries, show, output_file, vplot
from bokeh.plotting import figure, output_file, show
import pandas as pd

#request the list of all genres of movies on TMDB 
genre = requests.get('https://api.themoviedb.org/3/genre/movie/list?api_key='+TMDB_KEY).json()['genres']

#make a list of start date and end date of each month
month = [['Jan','2016-01-01','2016-01-31'],['Feb','2016-02-01','2016-02-29'],['Mar','2016-03-01','2016-03-31'],
         ['Apr','2016-04-01','2016-04-30'],['May','2016-05-01','2016-05-31'],['Jun','2016-06-01','2016-06-30'],
         ['Jul','2016-07-01','2016-07-31'],['Aug','2016-08-01','2016-08-31'],['Sep','2016-09-01','2016-09-30'],
         ['Oct','2016-10-01','2016-10-31'],['Nov','2016-11-01','2016-11-30'],['Dec','2016-12-01','2016-12-31']]

def get_genrenum(input):
    """ transfer the genre string input into genre id 
        accordingly,so that it is easy to query the 
        requests
    """
    for i in range(len(genre)):
        if genre[i]['name'].lower() == input.lower():
            return genre[i]['id']


def get_movie_genre(monthb,monthl,genrenum):
    """ the function returns the number of movies of certain 
        genre released in certain month through API requests
    """
    data = requests.get('https://api.themoviedb.org/3/discover/movie?api_key='+ TMDB_KEY +
                        '&primary_release_date.gte='+ monthb + '&primary_release_date.lte=' 
                       + monthl +'&with_genres='+ str(genrenum)).json()['total_results']
    return data

def get_all_movie(monthb,monthl):
    """ the function returns the number of movies released 
        in certain month through API requests
    """
    data = requests.get('https://api.themoviedb.org/3/discover/movie?api_key='+ TMDB_KEY +
                        '&primary_release_date.gte='+ monthb + '&primary_release_date.lte=' 
                        + monthl).json()['total_results']
    print('.')
    return data

def get_month_movie_genre(genrenum):
    """ the function returns the list of percentage of movies of certain genre
        released in each month
    """    
    monthdata = [round(get_movie_genre(i[1],i[2],genrenum)/get_all_movie(i[1],i[2])*100,2) for i in month]
    return monthdata

def genrebyseason(genrelist):
    """ the function uses bokeh library to draw line graph that 
        demonstrates the changes in percentage of movie releases by genre 
        over time in 2016
    """    
    x = [i[0] for i in month]
    print('Fetching Monthly Movies Data By Genres:')
    y = [get_month_movie_genre(get_genrenum(i)) for i in genrelist]
    p = figure(x_range = x, y_range = [0, max([max(i) for i in y]) + 10],
               title ='2016 Movie Trends', x_axis_label = 'month', 
               y_axis_label ='releases percentage(%)')
    color = ['#fbb4ae','#b3cde3','#ccebc5','#decbe4','#fed9a6']
    for i in range(len(genrelist)):
        p.line(x,y[i],legend = genrelist[i],
              line_color = color[i],line_width = 2)
    show(p)

def movielist(actor):
    """This function takes as input the name of the actor and returns as output two lists which represent the names and ids of movies that the actor has worked in"""
    #query the api endpoint to get id of the actor from the movie db
    actorendpoint='http://api.tmdb.org/3/search/person'
    parameters1={'api_key':TMDB_KEY,'query':actor}
    json_actorid=requests.get(actorendpoint,params=parameters1)
    actoridjson=json.loads(json_actorid.text)
    #get the actor id from the json data
    actorid=str(actoridjson['results'][0]['id'])
    #append the actor id to the api endpoint for scraping movie credits data for the actor
    movieendpoint='https://api.themoviedb.org/3/person/'+actorid+'/movie_credits'
    parameters2={'api_key':TMDB_KEY}
    json_movies_data=requests.get(movieendpoint,params=parameters2)
    actorjson=json_movies_data.json()
    #Get the list of movies from the returned json data
    movieslist=[mov['original_title'] for mov in actorjson['cast']]
    movieids=[]
    print('Fetching '+actor+' Movie List:')
    #use the movie names list to query the movie db api for movie ids
    for movie in movieslist:
        movieendpoint='http://api.tmdb.org/3/search/movie'
        parameters3={'api_key':TMDB_KEY,'query':movie}
        json_movieid=requests.get(movieendpoint,params=parameters3)
        movieidjson=json_movieid.json()
        movieid=str(movieidjson['results'][0]['id'])
        movieids.append(movieid)
        print('.',end='')
    print()
    #return the movie names and movie ids lists
    return movieslist,movieids

def movie_popularity(movieids,actor):
    """This function takes as input the list of movie ids in which the actor has worked in, the actor name, and returns a list of tuples which represent the release date year and profits for each movie in the input list """
    #query the movies api endpoint using the movie ids in the list
    movieendpoint='https://api.themoviedb.org/3/movie/'
    parameters4={'api_key':TMDB_KEY}
    movietuples=[]
    print('Analyzing '+actor+' Popularity:')
    #The measure of actor popularity for a particular year here is the sum of profits of all movies released in that year in which they have worked in
    for id in movieids:
        json_moviedata=requests.get(movieendpoint+id,params=parameters4)
        movie=json_moviedata.json()
        #filter out results where movies release date is absent, or absolute value of revenue is less than $100, and budget is less than $1000 (Possibly erroneous values)
        if movie['release_date']!='' and abs(movie['revenue'])>100 and movie['budget']>1000:
            movietuples.append((movie['revenue']-movie['budget'],movie['release_date']))
        print('.',end='')
    print()
    movietuples=[(tuples[0],datetime.strptime(tuples[1], '%Y-%m-%d').date().year) for tuples in movietuples]
    #return the list of tuples where each tuple represents the profit for each movie and the year of the movie release date
    return movietuples

def show_viz(datatuples,actor):
    """This function takes as input the list of tuples  which represent the profits and release date of each movie in which a actor has worked in and plots the visualization of the actor performance over time"""
    print("Creating the Data Visualization:")
    xvals=[v[1] for v in datatuples]
    yvals=[v[0] for v in datatuples]
    dat={'Year':xvals,'Profit':yvals}
    #create a dataframe from the input data with columns as year and profit
    dat1=pd.DataFrame(dat)
    #group the data by year to get the sum of profits of all movies by the actor for each year
    dat2=dat1.groupby(['Year']).sum()
    #Create the line graph
    p = Line(data=dat2,y='Profit', title=actor+" popularity over time",xlabel="Time",ylabel="Movie Profits($)")
    #Output the graph to a file
    output_file('actor_popularity.html')
    show(p)
   
def analysis1():
    """This function takes as input the list of 
       genres and calls the individual functions which analyze and 
       plot the data
    """
    genrelist = []
    num = input('Enter the number of genres you want to explore: ')
    for i in range(int(num)):
        genrelist.append(input('Enter the genre '+ str(i+1) +': '))
    genrebyseason(genrelist)

def analysis2(actor):
    """This function takes as input the name of the actor and calls the individual functions which analyze and plot the data"""
    #Get the list of movies and movie ids of the actor
    actormovies,movieids=movielist(actor)
    #The performance metric of the actor here is the profitability of the movies he/she has worked in
    #Get the time series data of the profitability of the actors movies over time
    actor_performance=movie_popularity(movieids,actor)
    #plot the vizualization using bokeh
    show_viz(actor_performance,actor)


def main():
    """The main function  which calls the analysis functions"""
    print('1. Analysis of the distribution of film releases by genre (e.g., Action, Comedy, Horror) throughout the year.')
    print('2. Analysis of the popularity of an actors films over that actors career')
    ip=input('Which analysis do you want to perform (Enter 1/2)')
    #if input is 1 perform Analysis 1 else perform analysis 2
    if ip=='1':
        analysis1()
    elif ip=='2':
        actor=input('Enter the name of the actor')
        analysis2(actor)
    else:
        print('Invalid Input')

if __name__ == "__main__":
    main()





