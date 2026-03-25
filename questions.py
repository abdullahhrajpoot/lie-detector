"""
questions.py — POLYTRUTH v5.0
Question bank, follow-up pools, and used-question cache.
"""

# ─────────────────────────────────────────────────────────────
# Global cache — mutated by session.py to prevent repeats
# ─────────────────────────────────────────────────────────────
USED_QUESTIONS: set = set()

# ─────────────────────────────────────────────────────────────
# PRIMARY QUESTION BANK (55 questions)
# ─────────────────────────────────────────────────────────────
QUESTION_BANK = [
    # 1
    "Walk me through the exact sequence of events on the last day you called in sick "
    "to work or school. Start from the moment you woke up.",

    # 2
    "Describe in precise detail what you were doing at 9pm exactly one week ago. "
    "Who was with you and what were you talking about?",

    # 3
    "Tell me about a time you were completely honest with someone even though it hurt "
    "them. What did you say, word for word, and how did they react?",

    # 4
    "Describe the last time you went through someone else's personal belongings — "
    "a phone, a bag, a drawer — without their knowledge or permission.",

    # 5
    "What is the biggest lie you have told in the past 12 months, and why did you "
    "decide that lie was necessary?",

    # 6
    "Think about the last time you broke a rule, a law, or a clear moral boundary. "
    "Describe exactly what happened and what you told yourself to justify it.",

    # 7
    "Recount the last time someone asked you a direct question and you deliberately "
    "gave them an incomplete or misleading answer. What was the question?",

    # 8
    "Describe in full detail the last time you cancelled plans with someone. "
    "What reason did you give them, and was that the real reason?",

    # 9
    "Tell me about the most recent conversation you had that you would not want "
    "recorded and replayed to the people who know you best.",

    # 10
    "Walk me through the last time you witnessed someone do something wrong and said "
    "nothing. What was happening and why did you stay silent?",

    # 11
    "Describe the last time you took something — an object, credit, an opportunity — "
    "that you knew was not entirely yours to take.",

    # 12
    "Recall the last time you looked at someone else's screen, messages, or documents "
    "without being invited to do so. What did you see?",

    # 13
    "Tell me about a promise you made in the last year that you have not kept. "
    "What exactly did you promise and what happened instead?",

    # 14
    "Describe the last time you pretended to feel an emotion you did not actually "
    "feel. What emotion was it and who were you performing it for?",

    # 15
    "What is something you have done that, if your closest family member found out "
    "today, would genuinely damage their opinion of you?",

    # 16
    "Walk me through the last purchase or financial transaction you made that you "
    "would feel uncomfortable explaining to someone who handles your money.",

    # 17
    "Describe the last time you blamed someone else for a mistake that was "
    "at least partly your own fault. What did you say?",

    # 18
    "Tell me about the last time you exaggerated your qualifications, experience, or "
    "achievements when talking to someone who could benefit from knowing the truth.",

    # 19
    "Recall a moment in the past six months when you acted one way in public and a "
    "completely different way in private. Describe both versions.",

    # 20
    "Describe the last time you read or listened to something private — a letter, "
    "a voicemail, a conversation — that was not meant for you.",

    # 21
    "Tell me about the last time you used information about someone to your own "
    "advantage without their knowledge that you were doing so.",

    # 22
    "When was the last time you manipulated a situation so that another person would "
    "reach a conclusion you had already decided on? Walk me through it.",

    # 23
    "Describe the last time you agreed with someone out loud while privately "
    "believing the exact opposite. What were they saying?",

    # 24
    "Tell me about a relationship in your life — personal or professional — where "
    "you are significantly less honest than you appear to be from the outside.",

    # 25
    "Recall the last time you let someone believe something about you that "
    "was not accurate. Did you correct it? Why or why not?",

    # 26
    "Describe the last time you sent a message — text, email, social media — "
    "and then immediately regretted the content or wished you could unsend it.",

    # 27
    "Walk me through the last time you told a child something that was not true. "
    "What was the lie and what was the honest version?",

    # 28
    "Tell me about the last time you took credit for work that was not entirely "
    "or primarily yours. How did the conversation go?",

    # 29
    "Describe a secret you are currently keeping from someone close to you. "
    "How long have you been keeping it and what would happen if they found out?",

    # 30
    "Recall the last time you used alcohol, medication, or another substance "
    "differently from how others around you believed you were using it.",

    # 31
    "Tell me about the last time you deliberately omitted crucial information "
    "from a conversation, knowing that omission changed its meaning entirely.",

    # 32
    "Describe the last time you changed your story — told different people "
    "different versions of the same event. What were the two versions?",

    # 33
    "What is something you have searched for online in the past month that you "
    "would be embarrassed to have publicly displayed?",

    # 34
    "Walk me through the last time you said 'I don't know' when in reality "
    "you did know, or at least strongly suspected the answer.",

    # 35
    "Describe the last time you deliberately let a misunderstanding persist because "
    "correcting it felt inconvenient or risky for you.",

    # 36
    "Tell me about the last time you made a decision that negatively affected "
    "someone else and chose not to tell them you were responsible.",

    # 37
    "Recall a time in the past year when you received praise or recognition for "
    "something that you privately felt you did not deserve.",

    # 38
    "Describe the last time you were in a meeting, group conversation, or public "
    "setting and deliberately withheld information that would have changed the outcome.",

    # 39
    "Tell me about the last time you were dishonest in a romantic or intimate "
    "context. What did you say or do?",

    # 40
    "Walk me through the last time you deleted messages, emails, files, or photos "
    "because you did not want someone else to find them.",

    # 41
    "Describe the last time you used someone else's login credentials, identity, "
    "or personal information without full explicit permission.",

    # 42
    "Tell me about a time you pretended not to have seen or received something — "
    "a message, a notification, an invitation — when you had seen it.",

    # 43
    "Recall the last time you gave advice you yourself do not follow. "
    "What was the advice and what do you actually do instead?",

    # 44
    "Describe the last time you borrowed something and returned it damaged or "
    "lost it entirely, and what you told the owner.",

    # 45
    "Tell me about the last time you said or implied you were somewhere you were not. "
    "Where did you say you were and where were you actually?",

    # 46
    "Walk me through the last time someone asked you how you were doing and your "
    "answer was significantly different from how you actually felt.",

    # 47
    "Describe the last time you agreed to something — a plan, a project, a commitment — "
    "while already planning not to follow through.",

    # 48
    "Tell me about the last time you expressed strong confidence in something "
    "you were privately very uncertain about.",

    # 49
    "Recall the last significant mistake you made at work or school. "
    "Who did you tell, and how did your account of events differ from what actually happened?",

    # 50
    "Describe the last time you helped someone primarily because of what you expected "
    "to get in return, while presenting it as purely selfless.",

    # 51
    "Tell me about the last time you felt genuine envy toward someone and "
    "how you behaved toward them in the hours immediately after.",

    # 52
    "Walk me through the last time you made up an excuse that you knew immediately "
    "was obviously false but delivered it anyway. What did you say?",

    # 53
    "Describe the last time you shared someone else's private information with "
    "a third party after telling that person their secret was safe with you.",

    # 54
    "Tell me about a time you deliberately triggered a negative emotional reaction "
    "in someone — jealousy, anxiety, guilt — and describe exactly how you did it.",

    # 55
    "Recall the last time you discovered you had been lied to about something serious. "
    "Did you confront the person? If not, describe what you chose to do instead.",

    # 56 (bonus)
    "Describe the last time you cheated at something — a game, a test, a competition — "
    "and explain what you told yourself to justify doing it.",

    # 57 (bonus)
    "Tell me about the last time you set a boundary with someone and then "
    "secretly crossed it yourself.",
]

# ─────────────────────────────────────────────────────────────
# FOLLOW-UP: DECEPTIVE TRACK (15 aggressive questions)
# ─────────────────────────────────────────────────────────────
FOLLOWUP_DECEPTIVE = [
    "Your previous answer showed elevated cognitive load markers. "
    "I need you to repeat the core of your answer but with more specific timestamps.",

    "The system flagged an inconsistency. Walk me through that event again "
    "from a completely different starting point — do not paraphrase your last answer.",

    "You used several distancing phrases in that response. "
    "Replace every use of 'they', 'that person', or 'the situation' with proper names and specifics.",

    "How many other people were present when this happened? "
    "Name each one of them and describe their exact role in the event.",

    "If I spoke to everyone you just mentioned right now, "
    "would their account of this event match yours detail for detail? "
    "Explain any discrepancies you anticipate.",

    "You paused before answering. What were you thinking about in that pause "
    "that you chose not to include in your answer?",

    "What is the single detail in that account that you are most nervous about "
    "having recorded and reviewed later?",

    "Walk me through what happened immediately after the event you described. "
    "Who did you talk to first and what exactly did you say?",

    "Your biometric stress indicators spiked significantly during that response. "
    "I'm going to need you to identify the moment in that story you found most difficult to narrate.",

    "Is there any version of that event where your behavior looks worse than you just described? "
    "Tell me that version.",

    "What physical evidence exists that could verify or contradict your account? "
    "Describe every piece you are aware of.",

    "You said the situation 'just happened'. "
    "What specific decisions did you make in the 24 hours before it that led directly to that moment?",

    "How many times have you rehearsed or mentally re-narrated this story before today?",

    "What is the one thing about this event that you have never told anyone and have no "
    "intention of including in any official account?",

    "On a scale of one to ten, how truthful was your answer? "
    "Justify your number with specifics, not generalities.",
]

# ─────────────────────────────────────────────────────────────
# FOLLOW-UP: TRUTHFUL TRACK (15 softer confirmatory questions)
# ─────────────────────────────────────────────────────────────
FOLLOWUP_TRUTHFUL = [
    "Your baseline biomarkers remained stable during that response. "
    "For completeness, can you identify the emotional tone you felt while answering?",

    "That account appeared consistent. Is there any additional context you feel "
    "would give a more complete picture of the situation?",

    "How long ago did this event occur, and has your understanding of it "
    "changed over time as you have reflected on it?",

    "Was there anyone else who witnessed this who you believe would describe it similarly to you?",

    "What did you learn about yourself from that experience?",

    "How did you feel immediately after the event you described, "
    "and has that feeling changed since then?",

    "Is there anything about how you handled that situation that you would change today?",

    "Your response was detailed and specific. "
    "How confident are you in the accuracy of the timeline you provided?",

    "Did the event you described have any lasting effects on the relationships involved? "
    "How are those relationships today?",

    "You answered that without significant hesitation. "
    "Is this something you think about often, or was today the first time you have narrated it?",

    "What would you want the record to show about your motivations in that situation?",

    "Was there a point during or after that event where you considered behaving differently? "
    "What held you to the path you chose?",

    "If someone who knows you well heard your account today, "
    "would they say it sounds consistent with the person they know?",

    "Is there anything you said in that account that you feel deserves more explanation "
    "than you had the chance to give?",

    "Thank you for that account. "
    "Is there anything else you want to place on the record voluntarily?",
]
