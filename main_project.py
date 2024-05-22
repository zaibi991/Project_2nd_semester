#  RSS Feed Filter
# Name:
# Collaborators:
# Time:

import feedparser
import string
import time
import threading
from project_util import translate_html
from mtTkinter import *
from datetime import datetime
import pytz


#-----------------------------------------------------------------------

#======================
# Code for retrieving and parsing
# Google and Yahoo News feeds
# Do not change this code

#======================

def process(url):
    """
    Fetches news items from the rss url and parses them.
    Returns a list of NewsStory-s.
    """
    feed = feedparser.parse(url)
    entries = feed.entries
    ret = []
    for entry in entries:
        guid = entry.guid
        title = translate_html(entry.title)
        link = entry.link
        description = translate_html(entry.description)
        pubdate = translate_html(entry.published)

        try:
            pubdate = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %Z")
            pubdate.replace(tzinfo=pytz.timezone("GMT"))
          #  pubdate = pubdate.astimezone(pytz.timezone('EST'))
          #  pubdate.replace(tzinfo=None)
        except ValueError:
            pubdate = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %z")

        newsStory = NewsStory(guid, title, description, link, pubdate)
        ret.append(newsStory)
    return ret

#======================
# Data structure design
#==================================================================

# Problem 1

# TODO: NewsStory
class NewsStory:
    def __init__(self, guid, title, description, link, pubdate):
        """
        Initialize a NewsStory object.

        Args:
        guid (str): Globally unique identifier for the news story.
        title (str): Title of the news story.
        description (str): Description of the news story.
        link (str): URL link to the news story.
        pubdate (datetime): Publication date of the news story.
        """
        self.guid = guid
        self.title = title
        self.description = description  # Adding the description attribute
        self.link = link
        self.pubdate = pubdate

    def get_guid(self):
        return self.guid

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def get_link(self):
        return self.link

    def get_pubdate(self):
        return self.pubdate


#==================================================================
class Trigger(object):
    def evaluate(self, story):
        """
        Returns True if an alert should be generated
        for the given news item, or False otherwise.
        """
        # DO NOT CHANGE THIS!
        raise NotImplementedError

    def get_name(self):
        return self.__class__.__name__

class PhraseTrigger(Trigger):
    def __init__(self, phrase):
        self.phrase = phrase.lower()

    def is_phrase_in(self, text):
        text = text.lower()
        for p in string.punctuation:
            text = text.replace(p, ' ')
        words = text.split()
        phrase_words = self.phrase.split()
        for i in range(len(words) - len(phrase_words) + 1):
            if phrase_words == words[i:i + len(phrase_words)]:
                return True
        return False

class TitleTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_title())

class DescriptionTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_description())

class TimeTrigger(Trigger):
    def __init__(self, time_string):
        est = pytz.timezone("EST")
        self.time = est.localize(datetime.strptime(time_string, "%d %b %Y %H:%M:%S"))

class BeforeTrigger(TimeTrigger):
    def evaluate(self, story):
        return story.get_pubdate().replace(tzinfo=pytz.timezone("EST")) < self.time

class AfterTrigger(TimeTrigger):
    def evaluate(self, story):
        return story.get_pubdate().replace(tzinfo=pytz.timezone("EST")) > self.time

class NotTrigger(Trigger):
    def __init__(self, trigger):
        self.trigger = trigger

    def evaluate(self, story):
        return not self.trigger.evaluate(story)

class AndTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) and self.trigger2.evaluate(story)

class OrTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) or self.trigger2.evaluate(story)

def read_trigger_config(filename):
    trigger_file = open(filename, 'r')
    lines = []
    for line in trigger_file:
        line = line.rstrip()
        if not (len(line) == 0 or line.startswith('//') or line.startswith('#')):
            lines.append(line)
    
    triggers = {}
    trigger_list = []

    for line in lines:
        parts = line.split(',')
        if len(parts) < 2:
            print(f"Invalid line (too short): {line}")
            continue

        trigger_name = parts[0].strip()
        trigger_type = parts[1].strip()

        if trigger_type == 'TitleTrigger':
            if len(parts) != 3:
                print(f"Invalid line (incorrect number of arguments for TitleTrigger): {line}")
                continue
            triggers[trigger_name] = TitleTrigger(parts[2].strip())
            print(f"Created TitleTrigger: {trigger_name} with phrase {parts[2].strip()}")

        elif trigger_type == 'DescriptionTrigger':
            if len(parts) != 3:
                print(f"Invalid line (incorrect number of arguments for DescriptionTrigger): {line}")
                continue
            triggers[trigger_name] = DescriptionTrigger(parts[2].strip())
            print(f"Created DescriptionTrigger: {trigger_name} with phrase {parts[2].strip()}")

        elif trigger_type == 'BeforeTrigger':
            if len(parts) != 3:
                print(f"Invalid line (incorrect number of arguments for BeforeTrigger): {line}")
                continue
            triggers[trigger_name] = BeforeTrigger(parts[2].strip())
            print(f"Created BeforeTrigger: {trigger_name} with date {parts[2].strip()}")

        elif trigger_type == 'AfterTrigger':
            if len(parts) != 3:
                print(f"Invalid line (incorrect number of arguments for AfterTrigger): {line}")
                continue
            triggers[trigger_name] = AfterTrigger(parts[2].strip())
            print(f"Created AfterTrigger: {trigger_name} with date {parts[2].strip()}")

        elif trigger_type == 'NotTrigger':
            if len(parts) != 3:
                print(f"Invalid line (incorrect number of arguments for NotTrigger): {line}")
                continue
            if parts[2].strip() not in triggers:
                print(f"Invalid trigger name for NotTrigger: {parts[2].strip()}")
                continue
            triggers[trigger_name] = NotTrigger(triggers[parts[2].strip()])
            print(f"Created NotTrigger: {trigger_name} negating {parts[2].strip()}")

        elif trigger_type == 'AndTrigger':
            if len(parts) != 4:
                print(f"Invalid line (incorrect number of arguments for AndTrigger): {line}")
                continue
            if parts[2].strip() not in triggers or parts[3].strip() not in triggers:
                print(f"Invalid trigger names for AndTrigger: {parts[2].strip()}, {parts[3].strip()}")
                continue
            triggers[trigger_name] = AndTrigger(triggers[parts[2].strip()], triggers[parts[3].strip()])
            print(f"Created AndTrigger: {trigger_name} combining {parts[2].strip()} and {parts[3].strip()}")

        elif trigger_type == 'OrTrigger':
            if len(parts) != 4:
                print(f"Invalid line (incorrect number of arguments for OrTrigger): {line}")
                continue
            if parts[2].strip() not in triggers or parts[3].strip() not in triggers:
                print(f"Invalid trigger names for OrTrigger: {parts[2].strip()}, {parts[3].strip()}")
                continue
            triggers[trigger_name] = OrTrigger(triggers[parts[2].strip()], triggers[parts[3].strip()])
            print(f"Created OrTrigger: {trigger_name} combining {parts[2].strip()} and {parts[3].strip()}")

        elif trigger_type == 'ADD':
            for name in parts[2:]:
                if name.strip() not in triggers:
                    print(f"Invalid trigger name in ADD: {name.strip()}")
                else:
                    trigger_list.append(triggers[name.strip()])
                    print(f"Added trigger to list: {name.strip()}")

    return trigger_list


def filter_stories(stories, triggerlist, cont):
    filtered_stories = []
    for story in stories:
        cont.insert(END, f"Checking story: {story.get_title()}\n")
        for trigger in triggerlist:
            cont.insert(END, f"  Against trigger: {trigger.get_name()}\n")
            if trigger.evaluate(story):
                cont.insert(END, f"    Trigger {trigger.get_name()} matched!\n")
                filtered_stories.append(story)
                get_cont(story, cont)
                break
    return filtered_stories

def get_cont(newstory, cont):
    cont.insert(END, f"{newstory.get_title()}\n", "title")
    cont.insert(END, f"Published at: {newstory.get_pubdate().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    cont.insert(END, f"{newstory.get_description()}\n")
    cont.insert(END, f"{newstory.get_link()}\n\n")
    cont.insert(END, "*********************************************************************\n", "title")

def main_thread(master):
    try:
        triggerlist = read_trigger_config('triggers.txt')
        SLEEPTIME = 120
        
        frame = Frame(master)
        frame.pack(side=BOTTOM)
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT, fill=Y)

        t = "Google & Yahoo Top News"
        title = StringVar()
        title.set(t)
        ttl = Label(master, textvariable=title, font=("Helvetica", 18))
        ttl.pack(side=TOP)
        cont = Text(master, font=("Helvetica", 14), yscrollcommand=scrollbar.set)
        cont.pack(side=BOTTOM)
        button = Button(frame, text="Exit", command=root.destroy)
        button.pack(side=BOTTOM)
        guidShown = []

        def update_gui():
            stories = process("http://news.google.com/news?output=rss")
            filtered_stories = filter_stories(stories, triggerlist, cont)
            for story in filtered_stories:
                get_cont(story, cont)
            master.after(SLEEPTIME * 1000, update_gui)
    


        update_gui()

    except Exception as e:
        cont.insert(END, f"Error: {e}\n")

if __name__ == '__main__':
    root = Tk()
    root.title("Some RSS parser")
    thread = threading.Thread(target=main_thread, args=(root,))
    thread.start()
    root.mainloop()



if __name__ == '__main__':
    root = Tk()
    root.title("Some RSS parser")
    thread = threading.Thread(target=main_thread, args=(root,))
    thread.start()
    root.mainloop()