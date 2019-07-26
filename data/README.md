# Data sets

## Facebook datasets

### Facebook-fact-check
This dataset is original dataset provided BuzzFeedNews.
All urls come from FaceBook posts and are about 2016 the US election.
The urls are labelled by BuzzFeedNews journalists.

### BuzzFeed_fb_urls_parsed
This is a set of parsed urls from Facebook-fact-check.
It contains original FaceBook post urls, the actual urls, and labels.
Only 'most true' labels are relabelled as 1(Real news) and others as 0(Fake news).
1075 out of 2283 were parsed and 998 of them are labelled as 1 and 77 are labelled as 0.
Issue: only a small portion of tuples are 0s. 

## data_from_Kaggle
This dataset includes around 4k many urls with labels.
Issue: urls with 0 labels are coming from only three news sources and all trusty news sources have 1 labelled urls.

## fakeNewsNet_data
This dataset includes urls with labels from Politifact Gossipcop.
Issue: some urls seem to be old and not available anymore.
