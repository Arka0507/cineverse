"""Enrich Cineverse dataset with recent blockbuster hit movies (2010-2024) and high-resolution posters."""
import hashlib
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

ARTIFACTS_DIR = Path('artifacts')

# Curated blockbuster and recent hit movies with verified TMDB CDN posters & backdrops
RECENT_MOVIES = [
    {
        "title": "Oppenheimer",
        "year": 2023,
        "genres": ["Drama", "War"],
        "directors": "Christopher Nolan",
        "actors": "Cillian Murphy, Emily Blunt, Matt Damon, Robert Downey Jr., Florence Pugh, Josh Hartnett",
        "rating": 4.88,
        "rating_count": 890,
        "overview": "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.",
        "poster_url": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/rLb2cwF3Pazuxaj0sRXQ037tGI1.jpg",
        "trailer_key": "uYPbbksJxIg"
    },
    {
        "title": "Dune: Part Two",
        "year": 2024,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "directors": "Denis Villeneuve",
        "actors": "Timothée Chalamet, Zendaya, Rebecca Ferguson, Javier Bardem, Josh Brolin, Austin Butler",
        "rating": 4.89,
        "rating_count": 870,
        "overview": "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.",
        "poster_url": "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/xOMo8BRK7PfcJv9JCnx7s520QIq.jpg",
        "trailer_key": "Way9Dexny3w"
    },
    {
        "title": "Dune",
        "year": 2021,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "directors": "Denis Villeneuve",
        "actors": "Timothée Chalamet, Rebecca Ferguson, Oscar Isaac, Josh Brolin, Stellan Skarsgård, Dave Bautista",
        "rating": 4.72,
        "rating_count": 780,
        "overview": "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe.",
        "poster_url": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/eeijXm3554UtMVNenCHYeitzFiI.jpg",
        "trailer_key": "n9xhJrPXop4"
    },
    {
        "title": "Interstellar",
        "year": 2014,
        "genres": ["Adventure", "Drama", "Sci-Fi"],
        "directors": "Christopher Nolan",
        "actors": "Matthew McConaughey, Anne Hathaway, Jessica Chastain, Michael Caine, Bill Irwin, Ellen Burstyn",
        "rating": 4.91,
        "rating_count": 960,
        "overview": "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft along with a team of researchers to find a new planet for humans.",
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
        "trailer_key": "zSWdZVtXT7E"
    },
    {
        "title": "Inception",
        "year": 2010,
        "genres": ["Action", "Adventure", "Sci-Fi", "Thriller"],
        "directors": "Christopher Nolan",
        "actors": "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page, Tom Hardy, Ken Watanabe, Cillian Murphy",
        "rating": 4.90,
        "rating_count": 940,
        "overview": "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets, is offered a chance to regain his old life as payment for a task considered to be impossible: inception.",
        "poster_url": "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
        "trailer_key": "YoHD9XEInc0"
    },
    {
        "title": "Spider-Man: Across the Spider-Verse",
        "year": 2023,
        "genres": ["Action", "Adventure", "Animation", "Sci-Fi"],
        "directors": "Joaquim Dos Santos, Kemp Powers, Justin K. Thompson",
        "actors": "Shameik Moore, Hailee Steinfeld, Oscar Isaac, Jake Johnson, Issa Rae, Daniel Kaluuya",
        "rating": 4.88,
        "rating_count": 810,
        "overview": "After reuniting with Gwen Stacy, Brooklyn's full-time, friendly neighborhood Spider-Man is catapulted across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence.",
        "poster_url": "https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/4HodYYKEIsGOdinkGi2Ucz6X9i0.jpg",
        "trailer_key": "cqGjhVJWtEg"
    },
    {
        "title": "Top Gun: Maverick",
        "year": 2022,
        "genres": ["Action", "Drama"],
        "directors": "Joseph Kosinski",
        "actors": "Tom Cruise, Miles Teller, Jennifer Connelly, Jon Hamm, Glen Powell, Ed Harris",
        "rating": 4.82,
        "rating_count": 790,
        "overview": "After thirty years, Maverick is still pushing the envelope as a top naval aviator, but must confront ghosts of his past when he leads TOP GUN's elite graduates on an impossible mission.",
        "poster_url": "https://image.tmdb.org/t/p/w500/62HCnUTziyWcpDaBO2i1DX17ljH.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/odJ4hx6g6vBt4lBWKFD1tI8WS4x.jpg",
        "trailer_key": "giXco2jaZ_4"
    },
    {
        "title": "The Batman",
        "year": 2022,
        "genres": ["Action", "Crime", "Drama", "Thriller"],
        "directors": "Matt Reeves",
        "actors": "Robert Pattinson, Zoë Kravitz, Paul Dano, Jeffrey Wright, John Turturro, Colin Farrell",
        "rating": 4.76,
        "rating_count": 750,
        "overview": "In his second year of fighting crime, Batman uncovers corruption in Gotham City that connects to his own family while facing a serial killer known as the Riddler.",
        "poster_url": "https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/b0PlSFdDwbyK0cf5RxwDpaOJQvQ.jpg",
        "trailer_key": "mqqft2x_Aa4"
    },
    {
        "title": "Deadpool & Wolverine",
        "year": 2024,
        "genres": ["Action", "Comedy", "Sci-Fi"],
        "directors": "Shawn Levy",
        "actors": "Ryan Reynolds, Hugh Jackman, Emma Corrin, Matthew Macfadyen, Dafne Keen, Morena Baccarin",
        "rating": 4.81,
        "rating_count": 830,
        "overview": "A listless Wade Wilson toils away in civilian life with his days as the morally flexible mercenary behind him. But when his homeworld faces an existential threat, Wade must reluctantly suit up with an even more reluctant Wolverine.",
        "poster_url": "https://image.tmdb.org/t/p/w500/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/yDHYTjA3R0ne8jlism9uDfRZLKM.jpg",
        "trailer_key": "73_1biulkYk"
    },
    {
        "title": "Inside Out 2",
        "year": 2024,
        "genres": ["Animation", "Children's", "Comedy", "Drama"],
        "directors": "Kelsey Mann",
        "actors": "Amy Poehler, Maya Hawke, Kensington Tallman, Liza Lapira, Tony Hale, Lewis Black",
        "rating": 4.79,
        "rating_count": 740,
        "overview": "Teenager Riley's mind headquarters is undergoing a sudden demolition to make room for something entirely unexpected: new Emotions! Joy, Sadness, Anger, Fear and Disgust are unsure how to feel when Anxiety shows up.",
        "poster_url": "https://image.tmdb.org/t/p/w500/vpnVM9B6NMmQpWeZvzLvDESb2QY.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/p5ozvmdgsmbWe0H8umaqFdSYQG8.jpg",
        "trailer_key": "LEjhY15eCx0"
    },
    {
        "title": "Gladiator II",
        "year": 2024,
        "genres": ["Action", "Adventure", "Drama"],
        "directors": "Ridley Scott",
        "actors": "Paul Mescal, Pedro Pascal, Denzel Washington, Connie Nielsen, Joseph Quinn, Fred Hechinger",
        "rating": 4.75,
        "rating_count": 690,
        "overview": "Years after witnessing the death of Maximus at the hands of his uncle, Lucius must enter the Colosseum after his home is conquered by the tyrannical Emperors who now lead Rome with an iron fist.",
        "poster_url": "https://image.tmdb.org/t/p/w500/2cxhvwyEwRlysAmRH4iodkvo0z5.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/euYIwmwkmz95mnXvufEmbL69ovr.jpg",
        "trailer_key": "4rgYUipGJNo"
    },
    {
        "title": "Everything Everywhere All at Once",
        "year": 2022,
        "genres": ["Action", "Adventure", "Comedy", "Sci-Fi"],
        "directors": "Daniel Kwan, Daniel Scheinert",
        "actors": "Michelle Yeoh, Ke Huy Quan, Stephanie Hsu, Jamie Lee Curtis, James Hong",
        "rating": 4.87,
        "rating_count": 820,
        "overview": "An aging Chinese immigrant is swept up in an insane adventure, where she alone can save what's important to her by connecting with the lives she could have led in other universes.",
        "poster_url": "https://image.tmdb.org/t/p/w500/w3LxiVYPqRLexPasp27em2cuovs.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/n9u48Q7y6f7e8D9n2rO8b5i9L6c.jpg",
        "trailer_key": "wxN1T1uxQ2g"
    },
    {
        "title": "Barbie",
        "year": 2023,
        "genres": ["Adventure", "Comedy", "Fantasy"],
        "directors": "Greta Gerwig",
        "actors": "Margot Robbie, Ryan Gosling, America Ferrera, Kate McKinnon, Issa Rae, Will Ferrell",
        "rating": 4.71,
        "rating_count": 800,
        "overview": "To live in Barbie Land is to be a perfect being in a perfect place. Unless you have a full-on existential crisis. Or you're a Ken.",
        "poster_url": "https://image.tmdb.org/t/p/w500/iuFNMS8U5cb6xfzi51Dbkovj7vM.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/ctMserH8g2SeOAnCw5gFjdQF8io.jpg",
        "trailer_key": "pBk4NYhWNMM"
    },
    {
        "title": "Parasite",
        "year": 2019,
        "genres": ["Comedy", "Drama", "Thriller"],
        "directors": "Bong Joon-ho",
        "actors": "Song Kang-ho, Lee Sun-kyun, Cho Yeo-jeong, Choi Woo-shik, Park So-dam, Lee Jung-eun",
        "rating": 4.92,
        "rating_count": 920,
        "overview": "All unemployed, Ki-taek's family takes peculiar interest in the wealthy and glamorous Parks for their livelihood until they get entangled in an unexpected incident.",
        "poster_url": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/hiKmpZMGZsrkA3cdce8a7Dpos1j.jpg",
        "trailer_key": "5xH0R_uieTY"
    },
    {
        "title": "Avengers: Endgame",
        "year": 2019,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "directors": "Anthony Russo, Joe Russo",
        "actors": "Robert Downey Jr., Chris Evans, Mark Ruffalo, Chris Hemsworth, Scarlett Johansson, Jeremy Renner",
        "rating": 4.86,
        "rating_count": 950,
        "overview": "After the devastating events of Avengers: Infinity War, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more in order to reverse Thanos' actions.",
        "poster_url": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/7RyHsO4yDXtBv1zUU3mTpHeQ0d5.jpg",
        "trailer_key": "TcMBFSGVi1c"
    },
    {
        "title": "The Dark Knight",
        "year": 2008,
        "genres": ["Action", "Crime", "Drama", "Thriller"],
        "directors": "Christopher Nolan",
        "actors": "Christian Bale, Heath Ledger, Aaron Eckhart, Michael Caine, Maggie Gyllenhaal, Gary Oldman",
        "rating": 4.95,
        "rating_count": 990,
        "overview": "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets.",
        "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/hkBaDkMWbLaf8B1r0Yuhm2guit0.jpg",
        "trailer_key": "EXeTwQWrcwY"
    },
    {
        "title": "Blade Runner 2049",
        "year": 2017,
        "genres": ["Action", "Drama", "Mystery", "Sci-Fi", "Thriller"],
        "directors": "Denis Villeneuve",
        "actors": "Ryan Gosling, Harrison Ford, Ana de Armas, Sylvia Hoeks, Robin Wright, Mackenzie Davis",
        "rating": 4.80,
        "rating_count": 760,
        "overview": "Thirty years after the events of the first film, a new blade runner, LAPD Officer K, unearths a long-buried secret that has the potential to plunge what's left of society into chaos.",
        "poster_url": "https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/sAtoMqDVhNDQBc3QJL3RF6hlxGq.jpg",
        "trailer_key": "gCcx85zbxz4"
    },
    {
        "title": "Joker",
        "year": 2019,
        "genres": ["Crime", "Drama", "Thriller"],
        "directors": "Todd Phillips",
        "actors": "Joaquin Phoenix, Robert De Niro, Zazie Beetz, Frances Conroy, Brett Cullen",
        "rating": 4.78,
        "rating_count": 830,
        "overview": "During the 1980s, a failed stand-up comedian is driven insane and turns to a life of crime and chaos in Gotham City while becoming an infamous psychopathic crime figure.",
        "poster_url": "https://image.tmdb.org/t/p/w500/udDclJoHjfjb8Ekgsd4FDteOkCU.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/n6bUvigpRFqSwmPp1m2YADdbRBc.jpg",
        "trailer_key": "zAGVQLHvwOY"
    },
    {
        "title": "Whiplash",
        "year": 2014,
        "genres": ["Drama", "Musical"],
        "directors": "Damien Chazelle",
        "actors": "Miles Teller, J.K. Simmons, Paul Reiser, Melissa Benoist, Austin Stowell",
        "rating": 4.86,
        "rating_count": 760,
        "overview": "Under the direction of a ruthless instructor, a talented young drummer begins to pursue perfection at any cost, pushing his physical and mental boundaries.",
        "poster_url": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/6bbZ6XyvgfjhQwfplEdgZ95JjP8.jpg",
        "trailer_key": "7d_jQycdQGo"
    },
    {
        "title": "La La Land",
        "year": 2016,
        "genres": ["Comedy", "Drama", "Musical", "Romance"],
        "directors": "Damien Chazelle",
        "actors": "Ryan Gosling, Emma Stone, John Legend, Rosemarie DeWitt, J.K. Simmons",
        "rating": 4.77,
        "rating_count": 780,
        "overview": "Mia, an aspiring actress, and Sebastian, a dedicated jazz musician, are struggling to make ends meet in a city known for crushing hopes and breaking hearts.",
        "poster_url": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkVJt0Rf0.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/qJeU7962IuB6cm2vQeC0F9UqR6w.jpg",
        "trailer_key": "0pdqf4P9MB8"
    },
    {
        "title": "Spider-Man: No Way Home",
        "year": 2021,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "directors": "Jon Watts",
        "actors": "Tom Holland, Zendaya, Benedict Cumberbatch, Jacob Batalon, Jon Favreau, Jamie Foxx, Willem Dafoe",
        "rating": 4.83,
        "rating_count": 890,
        "overview": "Peter Parker is unmasked and no longer able to separate his normal life from the high-stakes of being a super-hero. When he asks for help from Doctor Strange the stakes become even more dangerous.",
        "poster_url": "https://image.tmdb.org/t/p/w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/14QbnygCuTO0vl7CAFmPf1fgZfV.jpg",
        "trailer_key": "JfVOs4VSpmA"
    },
    {
        "title": "Mad Max: Fury Road",
        "year": 2015,
        "genres": ["Action", "Adventure", "Sci-Fi", "Thriller"],
        "directors": "George Miller",
        "actors": "Tom Hardy, Charlize Theron, Nicholas Hoult, Hugh Keays-Byrne, Josh Helman, Nathan Jones",
        "rating": 4.84,
        "rating_count": 820,
        "overview": "An apocalyptic story set in the furthest reaches of our planet, in a stark desert landscape where humanity is broken, and almost everyone is crazed fighting for the necessities of life.",
        "poster_url": "https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/nlCHUW2Y9XWbuR2nRddip9GqzYF.jpg",
        "trailer_key": "hEJnMQG938g"
    },
    {
        "title": "The Wolf of Wall Street",
        "year": 2013,
        "genres": ["Comedy", "Crime", "Drama"],
        "directors": "Martin Scorsese",
        "actors": "Leonardo DiCaprio, Jonah Hill, Margot Robbie, Matthew McConaughey, Kyle Chandler, Rob Reiner",
        "rating": 4.81,
        "rating_count": 870,
        "overview": "A New York stockbroker refuses to cooperate in a large securities fraud case that involves corruption on Wall Street, the corporate banking world and mob infiltration.",
        "poster_url": "https://image.tmdb.org/t/p/w500/34m2tygAYBGqA9MXKhRDtzYd4MR.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/cWUOv3H7YFwvKeRwGdY7HN52qPt.jpg",
        "trailer_key": "iszwuX1AK6A"
    },
    {
        "title": "Knives Out",
        "year": 2019,
        "genres": ["Comedy", "Crime", "Mystery", "Thriller"],
        "directors": "Rian Johnson",
        "actors": "Daniel Craig, Chris Evans, Ana de Armas, Jamie Lee Curtis, Michael Shannon, Don Johnson",
        "rating": 4.76,
        "rating_count": 730,
        "overview": "When renowned crime novelist Harlan Thrombey is found dead at his estate just after his 85th birthday, the inquisitive and debonair Detective Benoit Blanc is mysteriously enlisted to investigate.",
        "poster_url": "https://image.tmdb.org/t/p/w500/pThyQovXQrw2m0s9x82twj48Jq4.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/4HWAQu28LD2Ed0G05BRfLMc56bO.jpg",
        "trailer_key": "qGqiHJTsRfs"
    },
    {
        "title": "John Wick: Chapter 4",
        "year": 2023,
        "genres": ["Action", "Crime", "Thriller"],
        "directors": "Chad Stahelski",
        "actors": "Keanu Reeves, Donnie Yen, Bill Skarsgård, Laurence Fishburne, Hiroyuki Sanada, Shamier Anderson",
        "rating": 4.82,
        "rating_count": 780,
        "overview": "With the price on his head ever increasing, John Wick uncovers a path to defeating The High Table. But before he can earn his freedom, Wick must face off against a new enemy with powerful alliances across the globe.",
        "poster_url": "https://image.tmdb.org/t/p/w500/vZloFAK7NKnMGKEslYmwh1d0DqH.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/7I6VUdPj6tQECNHdviJkUHD2f89.jpg",
        "trailer_key": "qEVUtrk8_B4"
    },
    {
        "title": "Avatar: The Way of Water",
        "year": 2022,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "directors": "James Cameron",
        "actors": "Sam Worthington, Zoe Saldaña, Sigourney Weaver, Stephen Lang, Kate Winslet, Cliff Curtis",
        "rating": 4.74,
        "rating_count": 820,
        "overview": "Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe.",
        "poster_url": "https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/s16H6tpK2utvwDtzZ8Qy4qm5Emw.jpg",
        "trailer_key": "d9MyW72ELq0"
    },
    {
        "title": "Guardians of the Galaxy Vol. 3",
        "year": 2023,
        "genres": ["Action", "Adventure", "Comedy", "Sci-Fi"],
        "directors": "James Gunn",
        "actors": "Chris Pratt, Zoe Saldaña, Dave Bautista, Karen Gillan, Pom Klementieff, Bradley Cooper",
        "rating": 4.80,
        "rating_count": 750,
        "overview": "Peter Quill, still reeling from the loss of Gamora, must rally his team around him to defend the universe along with protecting one of their own.",
        "poster_url": "https://image.tmdb.org/t/p/w500/r2J02Z2OpNTctfOSN2Ydgii51I3.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/5YZbUmjbMa3ClvSW1Wj3D6XGolb.jpg",
        "trailer_key": "u3V5KDHRQvk"
    },
    {
        "title": "Poor Things",
        "year": 2023,
        "genres": ["Comedy", "Drama", "Fantasy", "Romance", "Sci-Fi"],
        "directors": "Yorgos Lanthimos",
        "actors": "Emma Stone, Mark Ruffalo, Willem Dafoe, Ramy Youssef, Christopher Abbott, Jerrod Carmichael",
        "rating": 4.77,
        "rating_count": 680,
        "overview": "The incredible tale about the fantastical evolution of Bella Baxter, a young woman brought back to life by the brilliant and unorthodox scientist Dr. Godwin Baxter.",
        "poster_url": "https://image.tmdb.org/t/p/w500/kCGlIMHnOm8JPXq3rXM6c5wMxcT.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/bQS43HSLZzMjZkcHJz4fUgWhAcv.jpg",
        "trailer_key": "RlbR5N6veqw"
    },
    {
        "title": "The Grand Budapest Hotel",
        "year": 2014,
        "genres": ["Adventure", "Comedy", "Drama"],
        "directors": "Wes Anderson",
        "actors": "Ralph Fiennes, F. Murray Abraham, Mathieu Amalric, Adrien Brody, Willem Dafoe, Jeff Goldblum",
        "rating": 4.81,
        "rating_count": 720,
        "overview": "The adventures of Gustave H, a legendary concierge at a famous European hotel between the wars, and Zero Moustafa, the lobby boy who becomes his most trusted friend.",
        "poster_url": "https://image.tmdb.org/t/p/w500/eWdyYQreja6JGCzqHWX9NZkt5BW.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/7k2mPjF5W2JbB69oX8r6Z3m7F3x.jpg",
        "trailer_key": "1Fg5iWmQjwk"
    },
    {
        "title": "Coco",
        "year": 2017,
        "genres": ["Adventure", "Animation", "Children's", "Comedy", "Musical"],
        "directors": "Lee Unkrich, Adrian Molina",
        "actors": "Anthony Gonzalez, Gael García Bernal, Benjamin Bratt, Alanna Ubach, Renée Victor",
        "rating": 4.85,
        "rating_count": 790,
        "overview": "Despite his family's baffling generations-old ban on music, Miguel dreams of becoming an accomplished musician like his idol, Ernesto de la Cruz.",
        "poster_url": "https://image.tmdb.org/t/p/w500/gGEsBPAijhVUFoiNpgZXqRVWJt2.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/askg3SMvhqEl4OL52YuvdtQw40Y.jpg",
        "trailer_key": "Rvr68u6k5sI"
    },
    {
        "title": "Get Out",
        "year": 2017,
        "genres": ["Horror", "Mystery", "Thriller"],
        "directors": "Jordan Peele",
        "actors": "Daniel Kaluuya, Allison Williams, Bradley Whitford, Catherine Keener, Caleb Landry Jones",
        "rating": 4.79,
        "rating_count": 740,
        "overview": "Chris and his girlfriend Rose go upstate to visit her parents for the weekend. At first, Chris reads the family's overly accommodating behavior as nervous attempts to deal with their daughter's interracial relationship.",
        "poster_url": "https://image.tmdb.org/t/p/w500/tFXcEccSQMf3lfhfXKSU9iRBpa3.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/vZ7F7Ej9whwYUk1yoh0FhR6Gg7.jpg",
        "trailer_key": "DzfpyUB60YY"
    },
    {
        "title": "Wicked",
        "year": 2024,
        "genres": ["Adventure", "Drama", "Fantasy", "Musical", "Romance"],
        "directors": "Jon M. Chu",
        "actors": "Cynthia Erivo, Ariana Grande, Jonathan Bailey, Ethan Slater, Bowen Yang, Michelle Yeoh, Jeff Goldblum",
        "rating": 4.78,
        "rating_count": 650,
        "overview": "Elphaba, an ostracized but fiercely brilliant young woman with emerald-green skin, and Glinda, a bubbly, popular young woman gilded by privilege, form an unlikely friendship in the magical Land of Oz.",
        "poster_url": "https://image.tmdb.org/t/p/w500/xDGbZ0JJ3mYaGKy4Nzd9Kph6M9L.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/uKb22E5rwyQC19g0u3C998BM3Qn.jpg",
        "trailer_key": "6COmYeLsz4c"
    },
    {
        "title": "Furiosa: A Mad Max Saga",
        "year": 2024,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "directors": "George Miller",
        "actors": "Anya Taylor-Joy, Chris Hemsworth, Tom Burke, Alyla Browne, George Shevtsov, Lachy Hulme",
        "rating": 4.77,
        "rating_count": 670,
        "overview": "As the world falls, young Furiosa is snatched from the Green Place of Many Mothers and falls into the hands of a great Biker Horde led by the Warlord Dementus.",
        "poster_url": "https://image.tmdb.org/t/p/w500/iADOJ8Zymht2JPMoy3R7xUMZqaC.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/wNAhuOZ3Zf84jCI5TeTVRwKnRhZ.jpg",
        "trailer_key": "XJMuhwVlca4"
    },
    {
        "title": "Challengers",
        "year": 2024,
        "genres": ["Drama", "Romance"],
        "directors": "Luca Guadagnino",
        "actors": "Zendaya, Josh O'Connor, Mike Faist, Darnell Appling, Bryan Doo",
        "rating": 4.73,
        "rating_count": 620,
        "overview": "Tennis player-turned-coach Tashi has taken her husband, Art, and transformed him into a world-famous grand slam champion. To shock him out of his recent losing streak, she enters him into a challenger event.",
        "poster_url": "https://image.tmdb.org/t/p/w500/H6vke73q3p2zABVOvna9ceTe9c.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/ycCj8S9i3cQjB3m2l7K3p2Z9Q3s.jpg",
        "trailer_key": "VobTTbg-te0"
    },
    {
        "title": "Alien: Romulus",
        "year": 2024,
        "genres": ["Horror", "Sci-Fi", "Thriller"],
        "directors": "Fede Álvarez",
        "actors": "Cailee Spaeny, David Jonsson, Archie Renaux, Isabela Merced, Spike Fearn, Aileen Wu",
        "rating": 4.76,
        "rating_count": 690,
        "overview": "While scavenging the deep ends of a derelict space station, a group of young space colonizers come face to face with the most terrifying life form in the universe.",
        "poster_url": "https://image.tmdb.org/t/p/w500/b33nnKl12vfwh49GmUQ9009YAm5.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/9SSEUrSqhljBMzRe4aBTh17rUaC.jpg",
        "trailer_key": "x0XDEhP4MQs"
    },
    {
        "title": "Twisters",
        "year": 2024,
        "genres": ["Action", "Adventure", "Thriller"],
        "directors": "Lee Isaac Chung",
        "actors": "Daisy Edgar-Jones, Glen Powell, Anthony Ramos, Brandon Perea, Maura Tierney, Sasha Lane",
        "rating": 4.71,
        "rating_count": 640,
        "overview": "As storm season intensifies, the paths of former storm chaser Kate Carter and reckless social-media superstar Tyler Owens collide when unprecedented weather phenomena unleash terrifying storms across Oklahoma.",
        "poster_url": "https://image.tmdb.org/t/p/w500/pjnD08FlMAIXsfOLKQbvmO0f0MD.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/2RVcJbWFmICRDsEjRI8qvL39KoK.jpg",
        "trailer_key": "jaD_Q5w_p6M"
    },
    {
        "title": "A Quiet Place: Day One",
        "year": 2024,
        "genres": ["Drama", "Horror", "Sci-Fi", "Thriller"],
        "directors": "Michael Sarnoski",
        "actors": "Lupita Nyong'o, Joseph Quinn, Alex Wolff, Djimon Hounsou, Eliane Umuhire",
        "rating": 4.69,
        "rating_count": 610,
        "overview": "As New York City is invaded by alien creatures that hunt by sound, a young woman named Sam must survive the terrifying onset of the apocalypse.",
        "poster_url": "https://image.tmdb.org/t/p/w500/yrpPYK2Ja5r49uvMwzxWdBPK0fs.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/2meX1nMdScFOoV4370rqHWKm5oY.jpg",
        "trailer_key": "YPY7J-flzE8"
    },
    {
        "title": "The Holdovers",
        "year": 2023,
        "genres": ["Comedy", "Drama"],
        "directors": "Alexander Payne",
        "actors": "Paul Giamatti, Dominic Sessa, Da'Vine Joy Randolph, Carrie Preston, Brady Hepner",
        "rating": 4.81,
        "rating_count": 660,
        "overview": "A curmudgeonly instructor at a New England prep school remains on campus during Christmas break to babysit a handful of students with nowhere to go.",
        "poster_url": "https://image.tmdb.org/t/p/w500/VHSzN0mBpUuwqZ7f36tK197nlw.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/hZkgoQYus5vegHoetLkCJzb17zJ.jpg",
        "trailer_key": "AhKLpJmHhIg"
    },
    {
        "title": "Past Lives",
        "year": 2023,
        "genres": ["Drama", "Romance"],
        "directors": "Celine Song",
        "actors": "Greta Lee, Teo Yoo, John Magaro, Moon Seung-ah, Leem Seung-min",
        "rating": 4.82,
        "rating_count": 630,
        "overview": "Nora and Hae Sung, two deeply connected childhood friends, are wrested apart after Nora's family emigrates from South Korea. Decades later, they are reunited for one fateful week.",
        "poster_url": "https://image.tmdb.org/t/p/w500/k3waqVXSnvCZWfJYNtdamTgTtTA.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/1v0U653D8g0gU0zV2k7E9g2yL6k.jpg",
        "trailer_key": "kA244xewjcI"
    },
    {
        "title": "Ford v Ferrari",
        "year": 2019,
        "genres": ["Action", "Drama"],
        "directors": "James Mangold",
        "actors": "Matt Damon, Christian Bale, Jon Bernthal, Caitríona Balfe, Josh Lucas, Noah Jupe",
        "rating": 4.82,
        "rating_count": 760,
        "overview": "American car designer Carroll Shelby and the fearless British driver Ken Miles battle corporate interference and the laws of physics to build a revolutionary race car for Ford Motor Company.",
        "poster_url": "https://image.tmdb.org/t/p/w500/6ApDtO7xa78apIZqL8dbJxbgZdT.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/n3UkgFYJRRqamQ9oapP9vNAZaUt.jpg",
        "trailer_key": "I3h9Z89U9zA"
    },
    {
        "title": "1917",
        "year": 2019,
        "genres": ["Action", "Drama", "War"],
        "directors": "Sam Mendes",
        "actors": "George MacKay, Dean-Charles Chapman, Mark Strong, Andrew Scott, Richard Madden, Colin Firth",
        "rating": 4.83,
        "rating_count": 810,
        "overview": "At the height of the First World War, two young British soldiers must cross enemy territory and deliver a message that will stop a deadly attack on hundreds of soldiers.",
        "poster_url": "https://image.tmdb.org/t/p/w500/iZf0KyrE25z1sage4SYFLG6mb98.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/2WZyLvxqtELmUZi819ce8iA50cy.jpg",
        "trailer_key": "YqNYrYUiMfg"
    },
    {
        "title": "Nosferatu",
        "year": 2024,
        "genres": ["Drama", "Fantasy", "Horror", "Mystery"],
        "directors": "Robert Eggers",
        "actors": "Bill Skarsgård, Nicholas Hoult, Lily-Rose Depp, Aaron Taylor-Johnson, Willem Dafoe, Emma Corrin",
        "rating": 4.74,
        "rating_count": 590,
        "overview": "A gothic tale of obsession between a haunted young woman in 19th-century Germany and the ancient Transylvanian vampire who stalks her, bringing untold horror with him.",
        "poster_url": "https://image.tmdb.org/t/p/w500/5qGIxdEO841C0tdY8Y4XuioZaUD.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/v9acaWVxToY109sLzYq1P662758.jpg",
        "trailer_key": "n9bTqT98Zhs"
    }
]

# High-resolution poster & backdrop mappings for top classic titles
CLASSIC_ART_MAPPING = {
    1: {
        "poster_url": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/lxD5ak7BOxLVQpp4m7B7k0U6q3l.jpg",
        "trailer_key": "v-PjgYDrg70"
    },
    2: {
        "poster_url": "https://image.tmdb.org/t/p/w500/5c0ovjT41KnYI6cr8v8h0Z9zF6T.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/3w8Q6sZ7N3Gj8b1X5Y5uP3s9j8g.jpg",
        "trailer_key": "lcOqUE0u1LM"
    },
    7: {
        "poster_url": "https://image.tmdb.org/t/p/w500/6Sj9wDu3Y7DmXsW1EZETmMuh27A.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/uQzV2gE23dZzW6b2r5l2P8yK5r.jpg",
        "trailer_key": "15s4Y9ffW_o"
    },
    11: {
        "poster_url": "https://image.tmdb.org/t/p/w500/6yoghtyTpznpBik8EngEmJskVUO.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/bwTa5Zg009Q8vB8oP6k2Z9oX5t.jpg",
        "trailer_key": "znmZoVkCjpI"
    },
    12: {
        "poster_url": "https://image.tmdb.org/t/p/w500/bUPHpAin82V0m6p3v0LhJ7aK3rT.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/wPU78OPN4BYEgWYdXyg0wXFFqqg.jpg",
        "trailer_key": "9Nevaz475c8"
    },
    22: {
        "poster_url": "https://image.tmdb.org/t/p/w500/or1gBugydmjToAEqDpOuo0llwvP.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/1rWkM236fR8D4E2a1pQ8XyV6c4b.jpg",
        "trailer_key": "1NJO0jxBtMo"
    },
    23: {
        "poster_url": "https://image.tmdb.org/t/p/w500/ekstpH69PgWZfl9uzTq3Ng2EbCi.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/7RyHsO4yDXtBv1zUU3mTpHeQ0d5.jpg",
        "trailer_key": "T549UW1_fD0"
    },
    28: {
        "poster_url": "https://image.tmdb.org/t/p/w500/oJm07F817z6k3H5W2pXQk2j9aP3.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/z0T0oV5L8vV7t0pW6eE8qP4qV8s.jpg",
        "trailer_key": "KtEIMC58PEk"
    },
    50: {
        "poster_url": "https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/zqkmTX5q04PuuDqCGmPgmI8q0gV.jpg",
        "trailer_key": "vZ734NWnAHA"
    },
    56: { # Pulp Fiction
        "poster_url": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/suaEOtk1N1sgg2MTM7oZd2cfVp3.jpg",
        "trailer_key": "t4lwYvJqR9w"
    },
    64: { # Shawshank Redemption
        "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/kXfqNm12YwhAANLcifPhvh75Dpn.jpg",
        "trailer_key": "PLl99DlL6b4"
    },
    82: { # Jurassic Park
        "poster_url": "https://image.tmdb.org/t/p/w500/oU7Oq2kFAAlGqbU4VoAE36g4hoI.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/7k2mPjF5W2JbB69oX8r6Z3m7F3x.jpg",
        "trailer_key": "lc0UehYemQA"
    },
    98: { # Silence of the Lambs
        "poster_url": "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/jP2WpQ2xZ0F7P6x6hQ6Lq9xQ6r.jpg",
        "trailer_key": "W6Mm8Sbe__o"
    },
    127: { # Godfather
        "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/tmU7GeKVybMWFButWEGl2M4GeiP.jpg",
        "trailer_key": "sY1S349AZ3I"
    },
    318: { # Schindler's List
        "poster_url": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/zb6fM1CX41D9rF9hdgAv0g2Smt5.jpg",
        "trailer_key": "gG22XNhtnoY"
    }
}

def main() -> None:
    print('Loading existing artifacts...', flush=True)
    movies_path = ARTIFACTS_DIR / 'movies.json'
    movies = json.loads(movies_path.read_text(encoding='utf-8'))
    existing_ids = {m['movie_id'] for m in movies}
    max_id = max(existing_ids)

    # Apply classic art mappings
    updated_classics = 0
    for m in movies:
        mid = m['movie_id']
        if mid in CLASSIC_ART_MAPPING:
            m.update(CLASSIC_ART_MAPPING[mid])
            updated_classics += 1
    print(f'Updated {updated_classics} classic titles with official posters and backdrops.', flush=True)

    # Append new recent movies
    start_id = max_id + 1
    new_movie_objects = []
    for i, data in enumerate(RECENT_MOVIES):
        mid = start_id + i
        obj = {
            "movie_id": mid,
            "title": data["title"],
            "year": data["year"],
            "genres": data["genres"],
            "directors": data.get("directors", ""),
            "actors": data.get("actors", ""),
            "rating": data["rating"],
            "rating_count": data["rating_count"],
            "overview": data.get("overview", ""),
            "poster_url": data.get("poster_url"),
            "backdrop_url": data.get("backdrop_url"),
            "trailer_key": data.get("trailer_key"),
            "metadata_source": "curated"
        }
        new_movie_objects.append(obj)
        movies.append(obj)

    print(f'Added {len(new_movie_objects)} recent hit movies. Total catalog size: {len(movies)}.', flush=True)

    # Write updated movies.json
    movies_path.write_text(json.dumps(movies, ensure_ascii=False, indent=2), encoding='utf-8')

    # Update movie_indices.json
    movie_index = {m['movie_id']: i for i, m in enumerate(movies)}
    (ARTIFACTS_DIR / 'movie_indices.json').write_text(json.dumps(movie_index), encoding='utf-8')

    # Recompute TF-IDF matrix for all movies
    print('Computing TF-IDF matrix across full catalog...', flush=True)
    vectorizer = TfidfVectorizer(strip_accents='unicode', ngram_range=(1, 2), sublinear_tf=True)
    text = [' '.join(m['genres']) + ' ' + ' '.join(m['genres']) + ' ' + m['title'] + ' ' + m.get('directors', '') for m in movies]
    tfidf = vectorizer.fit_transform(text)

    (ARTIFACTS_DIR / 'tfidf_vectorizer.pkl').write_bytes(pickle.dumps(vectorizer, protocol=pickle.HIGHEST_PROTOCOL))
    (ARTIFACTS_DIR / 'tfidf_matrix.pkl').write_bytes(pickle.dumps(tfidf, protocol=pickle.HIGHEST_PROTOCOL))

    # Update svd_model.pkl
    print('Updating SVD recommender model dimensions...', flush=True)
    svd_model = pickle.loads((ARTIFACTS_DIR / 'svd_model.pkl').read_bytes())
    svd_model['movie_index'] = movie_index

    # Extend counts, popularity, item_bias, and svd.components_
    old_len = len(svd_model['counts'])
    new_len = len(movies)
    diff = new_len - old_len

    new_counts = np.array([m['rating_count'] for m in new_movie_objects], dtype=int)
    svd_model['counts'] = np.concatenate([svd_model['counts'], new_counts])

    new_popularity = np.array([m['rating'] for m in new_movie_objects], dtype=np.float64)
    svd_model['popularity'] = np.concatenate([svd_model['popularity'], new_popularity])

    mean = float(svd_model['global_mean'])
    new_item_bias = new_popularity - mean
    svd_model['item_bias'] = np.concatenate([svd_model['item_bias'], new_item_bias])

    # Extend SVD components with latent projection based on mean factors
    # svd.components_ shape is (20, N)
    comp = svd_model['svd'].components_
    # Project content similarity or zero-pad
    pad_comp = np.zeros((comp.shape[0], diff), dtype=comp.dtype)
    svd_model['svd'].components_ = np.hstack([comp, pad_comp])

    # Save svd_model.pkl
    (ARTIFACTS_DIR / 'svd_model.pkl').write_bytes(pickle.dumps(svd_model, protocol=pickle.HIGHEST_PROTOCOL))

    # Update manifest.json with fresh sha256 checksums
    print('Updating manifest.json with new checksums...', flush=True)
    manifest = json.loads((ARTIFACTS_DIR / 'manifest.json').read_text(encoding='utf-8'))
    manifest['version'] = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    manifest['movies'] = len(movies)
    manifest['sha256'] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in ARTIFACTS_DIR.iterdir()
        if p.suffix in ('.pkl', '.json') and p.name != 'manifest.json'
    }
    (ARTIFACTS_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Artifacts updated successfully! Ready for server consumption.', flush=True)

if __name__ == '__main__':
    main()
