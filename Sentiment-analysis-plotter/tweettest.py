#!/user/PycharmProjects/KOKO/sentiment_analyser.py






import re
import os
import pandas as pd
import tweepy,csv
import matplotlib.pyplot as plt
from sentiment_analyser import *
from time import time
 


class TwitterPlot:

    def __init__(self):
        self.tweets = []
        self.tweetText = []
        self.positive = 0
        self.negative = 0
        self.neutral = 0
        self.no_tweets = 0
        self.term_search = 0


    def DownloadData(self):
        '''
        :return: Add authentication keys to access twitter api, return tweets saved in  extweets.csv
        '''

        # input for term to be searched and how many tweets to search
        self.term_search = input("Enter Keyword/Tag (eg : tesla): ")
        self.no_tweets = int(input("Enter no of tweets to search on : "))

        # Optional: use local dataset instead of Twitter API
        use_local = input("Use local dataset data/Tweets.csv? (y/N): ").strip().lower() == 'y'
        if use_local:
            csv_path = os.path.join(os.path.dirname(__file__), 'data', 'Tweets.csv')
            if not os.path.exists(csv_path):
                raise SystemExit(f"Local dataset not found at {csv_path}")
            df = pd.read_csv(csv_path, encoding='latin-1')
            # Expect columns 'text' and 'airline_sentiment'; fall back to any 'text' column present
            text_col = 'text' if 'text' in df.columns else df.columns[0]
            # Filter by keyword (case-insensitive), English only if such info exists; otherwise simple contains
            mask = df[text_col].astype(str).str.contains(self.term_search, case=False, na=False)
            subset = df[mask][text_col].head(self.no_tweets)
            if subset.empty:
                print("No matching rows found; taking first N rows from dataset instead.")
                subset = df[text_col].head(self.no_tweets)
            for raw in subset:
                self.tweetText.append(self.cleanTweet(str(raw)).encode('utf-8'))
            with open('extweets.csv', 'a', newline='') as csvFile:
                csv.writer(csvFile).writerow(self.tweetText)
            return

        # try v2 (bearer) first if provided; else fall back to v1.1 auth
        bearer = os.getenv('TWITTER_BEARER_TOKEN')

        csvFile = open('extweets.csv', 'a')
        csvWriter = csv.writer(csvFile)

        if bearer:
            client = tweepy.Client(bearer_token=bearer, wait_on_rate_limit=True)
            fetched = 0
            query = f"{self.term_search} lang:en -is:retweet"
            paginator = tweepy.Paginator(
                client.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=['lang']
            )
            for page in paginator:
                if not page.data:
                    continue
                for t in page.data:
                    if t.lang != 'en':
                        continue
                    self.tweetText.append(self.cleanTweet(t.text).encode('utf-8'))
                    fetched += 1
                    if fetched >= self.no_tweets:
                        break
                if fetched >= self.no_tweets:
                    break
        else:
            consumerKey = os.getenv('TWITTER_CONSUMER_KEY') or input('Enter Twitter consumer key: ')
            consumerSecret = os.getenv('TWITTER_CONSUMER_SECRET') or input('Enter Twitter consumer secret: ')
            accessToken = os.getenv('TWITTER_ACCESS_TOKEN') or input('Enter Twitter access token: ')
            accessTokenSecret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET') or input('Enter Twitter access token secret: ')
            auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
            auth.set_access_token(accessToken, accessTokenSecret)
            api = tweepy.API(auth, wait_on_rate_limit=True)
            try:
                self.tweets = tweepy.Cursor(
                    api.search_tweets,
                    q=self.term_search,
                    lang="en",
                    tweet_mode="extended"
                ).items(self.no_tweets)
                for tweet in self.tweets:
                    text = getattr(tweet, 'full_text', tweet.text)
                    self.tweetText.append(self.cleanTweet(text).encode('utf-8'))
            except tweepy.errors.Unauthorized:
                print("Twitter auth failed: Invalid or expired OAuth1 token.")
                manual_bearer = input('Enter Twitter Bearer Token (press Enter to skip): ').strip()
                if not manual_bearer:
                    raise SystemExit("Set TWITTER_BEARER_TOKEN for v2 or provide valid OAuth1 keys.")
                client = tweepy.Client(bearer_token=manual_bearer, wait_on_rate_limit=True)
                fetched = 0
                query = f"{self.term_search} lang:en -is:retweet"
                paginator = tweepy.Paginator(
                    client.search_recent_tweets,
                    query=query,
                    max_results=100,
                    tweet_fields=['lang']
                )
                for page in paginator:
                    if not page.data:
                        continue
                    for t in page.data:
                        if t.lang != 'en':
                            continue
                        self.tweetText.append(self.cleanTweet(t.text).encode('utf-8'))
                        fetched += 1
                        if fetched >= self.no_tweets:
                            break
                    if fetched >= self.no_tweets:
                        break

        csvWriter.writerow(self.tweetText)
        csvFile.close()

        # finding average of how people are reacting
        self.positive = self.percentage(self.positive, self.no_tweets)
        self.negative = self.percentage(self.negative, self.no_tweets)
        self.neutral = self.percentage(self.neutral, self.no_tweets)


    def cleanTweet(self, tweet):
        '''
        :param tweet: Extracted tweets
        :return: Clean tweets, removed of punctuations, special characters etc.
        '''
        # Remove Links, Special Characters etc from tweet
        pattern = r"(@[A-Za-z0-9_]+)|https?://\S+|[^0-9A-Za-z \t]"
        return ' '.join(re.sub(pattern, " ", tweet).split())

    def percentage(self, part, whole):
        '''
        :param part: Part of the calculation
        :param whole: Overall value in the calculation
        :return:
        '''
        temp = 100 * float(part) / float(whole)
        return float(round(temp,2))

    def plotPieChart(self, positive, negative, neutral,term_search,no_tweets):
        '''
        :param positive: No of Positive sentiments
        :param negative: No of Negative sentiments
        :param neutral: No of Neutral sentiments
        :param term_search: Twitter tag requested by the user to be searched
        :param no_tweets: No of tweet search requested by the user
        :return:
        '''
        posper = self.percentage(positive,self.no_tweets)
        negper = self.percentage(negative,self.no_tweets)
        neuper = self.percentage(neutral,self.no_tweets)

        labels = ['Positive [' + str(posper) + '%]', 'Negative [' + str(negper) + '%]',
                  'Neutral [' + str(neuper) + '%]']

        sizes = [positive, negative, neutral]
        colors = ['#1FDA9A', '#DB3340', '#3A9AD9']  #['yellowgreen', 'red', 'gold']
        patches, texts = plt.pie(sizes, colors=colors, startangle=90)
        plt.legend(patches, labels, loc="best")
        #plt.title('How people are reacting on ' + '#' + str(term_search).upper() + ' by analyzing ' + str(no_tweets) + ' Tweets.')
        plt.title('How people are reacting on #{} by analyzing [{}] tweets'.format(str(term_search).upper(),str(no_tweets)))
        plt.axis('equal')
        plt.tight_layout()
        plt.show()

    def updateValue(self,z):
        '''
        :param z: Calculated sentiment
        :return: Updated count
        '''
        if z == 'positive':
            self.positive += 1
        elif z == 'neutral':
            self.neutral += 1
        else:
            self.negative += 1


#TODO: Original code without multi-process takes longer to process
# if __name__== "__main__":
#
#     sa = TwitterPlot()
#     sa.DownloadData()
#     obj = SentimentAnalysis()
#
#     ST = time()
#
#     for tweet in sa.tweetText:
#         y = str(tweet,'utf-8')
#         z = obj.predict_sentiment(y)
#         print('for {} the sentiment is {}'.format(y, z))
#         sa.updateValue(z)
#
#     print( time() - ST )
#
#     sa.plotPieChart(sa.positive,sa.negative,sa.neutral,sa.term_search,sa.no_tweets)


if __name__ == '__main__':
    sa = TwitterPlot()
    sa.DownloadData()
    obj = SentimentAnalysis()
    ST = time()
    for tweet in sa.tweetText:
        y = str(tweet,'utf-8')
        _, z = obj.predict_sentiment(y)
        sa.updateValue(z)
    print(time()-ST)
    sa.plotPieChart(sa.positive,sa.negative,sa.neutral,sa.term_search,sa.no_tweets)

