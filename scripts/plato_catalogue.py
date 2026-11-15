"""Dramatic order, settings, and summaries for the Plato listings.

Imported by scripts/build_plato.py. Dates are dramatic dates (when the
conversation is set), not dates of composition. See the note printed on
the catalogue pages for the sources.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from plato_stories import STORY

# slug -> Greek title as printed from the Burnet texts.
GREEK = {
    "euthyphro": "Εὐθύφρων",
    "apology": "Ἀπολογία Σωκράτους",
    "crito": "Κρίτων",
    "phaedo": "Φαίδων",
    "cratylus": "Κρατύλος",
    "theaetetus": "Θεαίτητος",
    "sophist": "Σοφιστής",
    "statesman": "Πολιτικός",
    "parmenides": "Παρμενίδης",
    "philebus": "Φίληβος",
    "symposium": "Συμπόσιον",
    "phaedrus": "Φαῖδρος",
    "alcibiades-1": "Ἀλκιβιάδης αʹ",
    "alcibiades-2": "Ἀλκιβιάδης βʹ",
    "hipparchus": "Ἵππαρχος",
    "lovers": "Ἐρασταί",
    "theages": "Θεάγης",
    "charmides": "Χαρμίδης",
    "laches": "Λάχης",
    "lysis": "Λύσις",
    "euthydemus": "Εὐθύδημος",
    "protagoras": "Πρωταγόρας",
    "gorgias": "Γοργίας",
    "meno": "Μένων",
    "hippias-major": "Ἱππίας μείζων",
    "hippias-minor": "Ἱππίας ἐλάττων",
    "ion": "Ἴων",
    "menexenus": "Μενέξενος",
    "cleitophon": "Κλειτοφῶν",
    "republic": "Πολιτεία",
    "timaeus": "Τίμαιος",
    "critias": "Κριτίας",
    "minos": "Μίνως",
    "laws": "Νόμοι",
    "epinomis": "Ἐπινομίς",
    "letters": "Ἐπιστολαί",
}

ENGLISH = {
    "euthyphro": "Euthyphro",
    "apology": "Apology",
    "crito": "Crito",
    "phaedo": "Phaedo",
    "cratylus": "Cratylus",
    "theaetetus": "Theaetetus",
    "sophist": "Sophist",
    "statesman": "Statesman",
    "parmenides": "Parmenides",
    "philebus": "Philebus",
    "symposium": "Symposium",
    "phaedrus": "Phaedrus",
    "alcibiades-1": "Alcibiades I",
    "alcibiades-2": "Alcibiades II",
    "hipparchus": "Hipparchus",
    "lovers": "Lovers",
    "theages": "Theages",
    "charmides": "Charmides",
    "laches": "Laches",
    "lysis": "Lysis",
    "euthydemus": "Euthydemus",
    "protagoras": "Protagoras",
    "gorgias": "Gorgias",
    "meno": "Meno",
    "hippias-major": "Hippias Major",
    "hippias-minor": "Hippias Minor",
    "ion": "Ion",
    "menexenus": "Menexenus",
    "cleitophon": "Cleitophon",
    "republic": "Republic",
    "timaeus": "Timaeus",
    "critias": "Critias",
    "minos": "Minos",
    "laws": "Laws",
    "epinomis": "Epinomis",
    "letters": "Letters",
}

# Thrasyllan order, nine groups of four. Matches tlg001 to tlg036.
TETRALOGIES = [
    ("I", "Euthyphro, Apology, Crito, Phaedo",
     ["euthyphro", "apology", "crito", "phaedo"]),
    ("II", "Cratylus, Theaetetus, Sophist, Statesman",
     ["cratylus", "theaetetus", "sophist", "statesman"]),
    ("III", "Parmenides, Philebus, Symposium, Phaedrus",
     ["parmenides", "philebus", "symposium", "phaedrus"]),
    ("IV", "Alcibiades I and II, Hipparchus, Lovers",
     ["alcibiades-1", "alcibiades-2", "hipparchus", "lovers"]),
    ("V", "Theages, Charmides, Laches, Lysis",
     ["theages", "charmides", "laches", "lysis"]),
    ("VI", "Euthydemus, Protagoras, Gorgias, Meno",
     ["euthydemus", "protagoras", "gorgias", "meno"]),
    ("VII", "Hippias Major and Minor, Ion, Menexenus",
     ["hippias-major", "hippias-minor", "ion", "menexenus"]),
    ("VIII", "Cleitophon, Republic, Timaeus, Critias",
     ["cleitophon", "republic", "timaeus", "critias"]),
    ("IX", "Minos, Laws, Epinomis, Letters",
     ["minos", "laws", "epinomis", "letters"]),
]

# Shown on the library rows and in the "Love in this dialogue" box.
# Wording is fixed; the date line stays separate.
LOVE = {
    "parmenides": "A very young Socrates presents his theory of Forms to the old philosopher Parmenides, who takes it apart and then runs him through a hard logical workout. Loving the truth means letting even your dearest ideas be tested.",
    "protagoras": "Socrates is fresh from flirting with Alcibiades when a friend drags him off to hear the famous sophist Protagoras. They argue over whether virtue can be taught, and by the end each has swapped positions. Socrates tells the friend he forgot Alcibiades entirely, because wisdom is the greater beauty.",
    "alcibiades-1": "Socrates finally speaks to the proud young Alcibiades, the lover who stayed after all the others left. He shows him he isn't ready to lead Athens because he doesn't know himself. To love someone is to love their soul and help it see itself.",
    "alcibiades-2": "Socrates meets Alcibiades on his way to pray and warns him that people often ask the gods for things that ruin them. Love without wisdom can wish harm on what it loves.",
    "charmides": "Back from battle, Socrates meets the stunningly beautiful Charmides and catches a glimpse inside his cloak, which almost unsettles him. He steadies himself, and they try and fail to define self-control. Self-mastery is what lets love see instead of grab.",
    "laches": "Two fathers ask two generals, Laches and Nicias, whether their sons should learn armoured fighting. Socrates draws them into asking what courage is. To love something enough to stand firm for it, you must know what is truly worth fearing.",
    "lysis": "At a wrestling school, Socrates helps the shy Hippothales, who is in love with the boy Lysis. Instead of flattering Lysis, Socrates talks with him and his friend about what makes someone a friend, and they can't settle it. Every love points past the beloved toward a \"first beloved\", the good itself.",
    "euthydemus": "Socrates recounts two brothers who win every argument with ridiculous word traps while a young man watches. Cleverness that cares about winning loves no one; real teaching cares whether the other person becomes wise.",
    "hippias-major": "The vain sophist Hippias tries to define \"the beautiful\" and keeps failing under Socrates' questions. If you can't say what beauty is, love doesn't know what it's chasing.",
    "hippias-minor": "Socrates argues with Hippias over whether honest Achilles or wily Odysseus is the better man, and reaches a troubling paradox about doing wrong on purpose. The heart has to be ordered toward the good, not just skilled.",
    "ion": "A prize-winning reciter of Homer admits he is moved by poetry but can't explain it. Socrates says he is possessed, like a link in a magnetic chain from the Muse. Passion is a divine gift, but it isn't knowledge.",
    "gorgias": "At a dinner, Socrates faces the orator Gorgias, then the hot-headed Polus, then the ruthless Callicles, who mocks him for preferring philosophy to power. Socrates answers that flattery feeds what people want, real care gives them what's good, and it is better to suffer wrong than to do it.",
    "republic": "At a festival night in the port of Piraeus, Socrates is pressed by the angry Thrasymachus and then by Plato's brothers to prove justice is worth having. He builds a perfect city in words to see justice large. Desire, educated by reason, learns to love the Good, which lights up everything worth loving like the sun. The tyrant is love gone wrong: endless appetite and no friends.",
    "symposium": "At a drinking party for the poet Agathon, the guests each praise Love. Aristophanes says lovers are split halves seeking wholeness. Socrates tells what the priestess Diotima taught him: love is longing to possess the beautiful forever, rising from one body to all beauty, then to souls, laws and knowledge, and finally to Beauty itself. Then a drunk Alcibiades bursts in and confesses that Socrates refused his seduction. This is the centre of Plato on love.",
    "phaedrus": "Socrates and the young Phaedrus walk barefoot along a stream outside the city and lie down under a plane tree. Phaedrus reads a speech saying it's better to give yourself to someone who doesn't love you. Socrates answers that love is a divine madness: the soul is a charioteer with a noble horse and an unruly one, and the sight of the beloved regrows the soul's wings. Two lovers who rein in desire together rise toward the divine.",
    "menexenus": "Socrates recites a funeral speech he says he learned from Aspasia, praising the war dead. Love of country can be noble or mere flattery.",
    "cratylus": "Two friends argue whether names are natural or just convention, and Socrates offers playful etymologies, including for \"eros\". Words point to the truth, but love has to reach the thing itself.",
    "meno": "The young Meno asks whether virtue can be taught. Socrates leads a slave boy to work out a geometry proof and argues that learning is recollection. Then Anytus, who will help prosecute him, warns him darkly. The love of learning is the soul remembering what it already longs for.",
    "theaetetus": "Shortly before his trial, Socrates meets a gifted young mathematician and calls himself a midwife of souls. They test three definitions of knowledge and none survives. He loves the young by helping them birth their own thoughts and checking whether they're true.",
    "euthyphro": "Outside the court, Socrates meets Euthyphro, who is prosecuting his own father, and asks him what piety is. They can't decide whether the gods love what is holy because it's holy, or whether it's holy because they love it. Love has to aim at what is good in itself.",
    "sophist": "A visitor from Elea, a pupil of Parmenides, tracks down the sophist, the imitator of wisdom, and in doing so works out how falsehood is possible. To love wisdom you have to tell it apart from its counterfeit.",
    "statesman": "The same visitor defines the true ruler as a weaver who binds bold and gentle citizens together. Love and friendship are the threads that make a city whole.",
    "apology": "Socrates defends himself before 500 Athenian jurors. He says the oracle at Delphi sent him to question everyone, and he won't stop, even to save himself. He is condemned to death and tells them no harm can come to a good man. He loves the truth and his city more than his life.",
    "crito": "At dawn in prison, his old friend Crito says the escape is arranged and begs him to go. Socrates imagines the Laws of Athens speaking to him like parents, and he stays. Loyalty and love mean keeping faith even when it costs everything.",
    "phaedo": "On his last day, his friends gather. Socrates argues that the soul is immortal and that philosophy is a lifelong preparation for death. At sunset he drinks the hemlock calmly while his friends weep. The lover of wisdom goes home to what he loved all along.",
    "timaeus": "The day after the Republic conversation, the astronomer Timaeus describes how a good craftsman made the cosmos to be as much like himself as possible. Creation itself is an act of generous love.",
    "critias": "Critias begins the tale of ancient Athens and Atlantis, a proud empire that grew greedy and was punished by the gods. It breaks off unfinished. A people whose love turns to greed falls.",
    "philebus": "Socrates and young Protarchus weigh pleasure against wisdom and decide the good life is a measured mixture of both. Desire is good when reason sets its measure.",
    "laws": "Three old men, from Athens, Crete and Sparta, walk to a shrine of Zeus and draft laws for a new city. The lawgiver loves the citizens like a parent and leads mainly by persuasion and education, so that marriage, festivals and friendship bind the city together.",
    "epinomis": "The same three men discuss the wisdom that crowns the laws, namely number and the study of the heavens. Wonder at the ordered sky is love turned toward the divine.",
    "minos": "Socrates asks a companion what law is and argues that true law aims at the truth. Lawful order is a form of care.",
    "hipparchus": "Socrates presses a friend on whether love of gain is shameful and concludes that everyone loves the good, though few know what it is.",
    "lovers": "In a school, two rivals compete for a boy's attention, one an athlete and one well read. Socrates asks whether loving wisdom means knowing a lot. It means knowing how to make oneself and others better.",
    "theages": "A farmer brings his son to Socrates to learn wisdom. Socrates explains that his inner divine sign decides whom he can help. Being near a good teacher helps only when the student truly loves the good.",
    "cleitophon": "Cleitophon tells Socrates that he inspires people to virtue but never shows them how to reach it. Love of the good needs a path, not just a spark.",
    "letters": "Plato, now old, writes about his failed attempts to guide the rulers of Syracuse and his grief over his murdered friend Dion. Truth is kindled in the soul like a spark from long companionship, not from writing.",
}

# Dramatic order. Each item is (slug, when, unused).
# "when" is the date and setting. The listing text is LOVE.
PHASES = [
    ("Youth", "Before the Peloponnesian War", [
        ("parmenides",
         "c. 450 BC. The Great Panathenaea. Socrates is about twenty.",
         "Cephalus tells how, at the Great Panathenaea, he heard of a meeting at which Zeno read his book and the young Socrates answered with forms set apart from the things that share in them. Parmenides presses that answer until it is in trouble, then leads Socrates through what follows if the one is, and if it is not. The question is whether forms can be stated without contradiction. No doctrine is adopted. The exercise is the training itself."),
        ("protagoras",
         "c. 433 BC. Callias’ house. Alcibiades has just grown a beard. Nails allows 432 as well.",
         "Hippocrates wakes Socrates before dawn and begs to be introduced to Protagoras, who is staying at Callias’ house with Hippias and Prodicus. Before that audience Protagoras answers with a myth and a long speech, and by the end the two men have exchanged the positions they began with. The question is whether virtue can be taught, and whether the virtues are one thing. It is left open."),
    ]),
    ("The Peloponnesian War", "From Potidaea to the defeat of Athens", [
        ("alcibiades-1",
         "c. 432 BC. Alcibiades is about twenty, about to enter public life, before the campaign at Potidaea.",
         "After watching him for years, Socrates finally stops Alcibiades in the street, just as Alcibiades is about to offer himself to the city. Question by question he brings him to admit that he does not know what he would be advising Athens about, and the talk turns to the Delphic command. The question is what the self is that one must know before ruling anyone else. Alcibiades agrees that it is the soul, and that he still has to be educated."),
        ("charmides",
         "429 BC. Taureas’ palaestra, the morning after Socrates returns from Potidaea.",
         "The morning after his return from Potidaea, Socrates goes to Taureas’ palaestra, and Critias introduces Charmides as a young man remarkable for temperance. Socrates pretends to have a cure for the boy’s headache so that he can question him, then turns to Critias when Charmides’ answers run out. The question is what temperance is. Quietness, modesty, doing one’s own work, and a knowledge of knowledge all fail, yet Charmides still asks to be taught."),
        ("gorgias",
         "c. 427 BC. Gorgias is in Athens on his embassy. The dialogue also mentions later events, and some readers place the talk in 405, after Socrates had sat on the Council.",
         "Socrates and Chaerephon arrive at Callicles’ house just after Gorgias has finished a display, and they persuade him to submit to questions. When Gorgias is embarrassed, Polus takes up the defence, and Callicles then attacks the philosophic life in a long speech. The question is what rhetoric is for, and whether doing wrong is worse than suffering it. Socrates maintains that it is worse to do wrong, and he closes with a myth of judgment on the naked soul."),
        ("laches",
         "424 BC. Soon after the retreat from Delium. Nicias and Laches are both still alive.",
         "Lysimachus and Melesias, ashamed that their famous fathers left them no distinction of their own, invite Nicias and Laches to watch a display of fighting in armor and to advise them about their sons. The display turns into a dispute about courage, and they ask Socrates to join. The question is what courage is. Standing one’s ground, endurance, and knowledge of what is fearful all fail, and the generals agree to study with Socrates themselves."),
        ("lysis",
         "c. 421 BC. A new palaestra, at festival time. Menexenus is still a boy. The year is less firmly fixed than that of the Laches.",
         "On his way from the Academy to the Lyceum, Socrates is pulled into a new palaestra by Hippothales, who wants help talking to the boy Lysis and then hides to listen. Socrates converses first with Lysis and then with Menexenus while the lovers look on. The question is what makes one person another’s friend. Likeness, unlikeness, and the presence of the good are each undone, and Socrates says they have not yet found what a friend is."),
        ("hippias-major",
         "c. 420 BC. Hippias of Elis is in Athens, which the Peace of Nicias makes plausible.",
         "Hippias, proud of the speeches he has just given abroad, meets Socrates, who says that someone at home keeps asking him a rude question he cannot answer. They try one reply after another, Socrates reporting the absent critic’s objections, until Hippias loses patience and leaves. The question is what the beautiful itself is, as distinct from beautiful things. A fine girl, gold, the fitting, the useful, and the pleasant all fail, and the question stays open."),
        ("hippias-minor",
         "c. 420 BC. The same visit, after Hippias has given a display on Homer.",
         "Hippias has just given a display on Homer and declared Achilles the better man, truthful where Odysseus is a liar. Socrates will not let him go, and he walks him through cases of people who err on purpose and people who err because they cannot help it. The question is whether the voluntary wrongdoer is better than the involuntary one. The argument ties voluntary error to knowledge. Hippias refuses the conclusion, and Socrates says that he wavers too."),
        ("phaedrus",
         "c. 418 BC. By the Ilissus, while Phaedrus is still in Athens. Nails argues for 418 or 416. Others put the walk in 404, after he returned from exile.",
         "Phaedrus has been with Lysias and is walking outside the walls to learn a speech by heart. Socrates meets him, makes him read it aloud, and hears Lysias argue that a boy should favour the man who does not love him. Socrates answers with a speech of his own, then recants, head covered, in a myth of the soul as a charioteer. The question that remains is what makes any speech an art. They conclude that rhetoric without knowledge of souls, and of the truth, is no art."),
        ("symposium",
         "416 BC. Agathon’s house, the night after his first victory. Apollodorus retells the party some years later.",
         "Apollodorus, stopped on the road, retells a party at Agathon’s house the night after Agathon’s first victory, a story he had from Aristodemus. The guests send the flute girl away and each praise love. Socrates reports Diotima, and then Alcibiades arrives drunk and praises Socrates instead. The question is what love is and what it wants. Diotima’s answer is the desire to possess the good forever, rising from beautiful bodies to beauty itself, and the drinking lasts until dawn."),
        ("ion",
         "c. 414 BC. Ion of Ephesus has just come from a contest. Ephesus is still spoken of as under Athens, so before the revolt of 412.",
         "Socrates meets the rhapsode Ion, just crowned at Epidaurus and full of Homer. He gets Ion to admit that he dozes through every other poet, and that he cannot name an art which would also make him a general, a doctor, and a charioteer. The question is whether this power is a craft or something else. Socrates offers a chain of divine possession from the Muse to the poet to the performer to the crowd, and Ion takes the grander title."),
        ("euthydemus",
         "c. 412 BC. The Lyceum. Crito asks about two brothers he has just seen. Some prefer 418, before the exiles from Thurii arrived.",
         "Crito has seen Socrates hemmed in by a crowd at the Lyceum, and the next day he asks who the two strangers were. Socrates narrates how Euthydemus and Dionysodorus put on a display for the boy Clinias and for Ctesippus, overturning every answer, while he himself questioned Clinias in the intervals. The question is whether their eristic is wisdom, and what knowledge would actually make a person happy. The display is left empty, and Socrates tells Crito not to let such men drive him off philosophy."),
        ("republic",
         "c. 411 BC. The Piraeus, at the new festival of Bendis. A date of 421, in the Peace of Nicias, and one of 429 are also defended. Nails argues that no single year fits every detail.",
         "Socrates goes down to the Piraeus for the new festival of Bendis, and Polemarchus’ slave catches him on the road home so that he spends the night at Cephalus’ house. The old man talks about wealth and leaves. Polemarchus, Thrasymachus, and then Glaucon and Adeimantus take up the argument and will not let Socrates go. The question is what justice is, and whether the just life is the happier. He builds a city in speech, finds justice where each part does its own work, and closes the ten books with the myth of Er."),
        ("timaeus",
         "c. 411 BC. The next day, if the opening is read as continuing the Republic. The summary Socrates gives does not match that dialogue in every particular.",
         "The day after a conversation about the best city, Timaeus, Critias, and Hermocrates return to repay Socrates with a feast of speeches. Critias recalls a tale Solon brought from Egypt, of Athens once defeating Atlantis, and he asks Timaeus to begin from the origin of the world. The question is what account can be given of the cosmos and of human beings. Timaeus offers a likely story of the craftsman, the world soul, and the body, and he stops once mortal creatures have been fitted together."),
        ("critias",
         "c. 411 BC. The same day, after Timaeus has finished.",
         "The same company turns from cosmology to narrative, and Critias takes the part he had reserved. He describes Athens as it was when Athena and Hephaestus allotted it, and Atlantis as it grew rich, canal-cut, and corrupt. The tale was promised as the true deeds of the city Socrates had described the day before. Zeus has called the gods together and is about to speak when the text breaks off."),
        ("theages",
         "c. 409 BC. Demodocus brings his son after the general Thrasyllus has left for Ionia. Traditionally doubted.",
         "Demodocus brings his son Theages in from the country because the boy is set on becoming great in the city and will not take up his father’s life. Socrates walks him through the teachers he might hire, and Theages still asks to be taken on as a companion. The question is whether Socrates has an art of making people wise. He says he has none, only a divine sign that sometimes forbids a companionship, and Theages asks to stay even on that condition."),
        ("alcibiades-2",
         "c. 407 BC. Alcibiades is on his way to pray, after his return to Athens and before Notium. The dialogue quotes a play produced in 409. Traditionally doubted.",
         "Socrates falls in with Alcibiades on the way to a sacrifice and walks with him toward the temple. He will not let the prayer be made until they have asked what a man who does not know his own good is likely to request of the gods. The question is whether it is safe to pray for particular things. A Spartan prayer, which asks only for what is noble, is preferred, and Alcibiades puts the sacrifice off."),
    ]),
    ("Later years", "After the war, before the trial", [
        ("meno",
         "402 BC. Meno is Anytus’ guest in Athens, before he leaves with Cyrus’ expedition.",
         "Meno, a Thessalian guest of Anytus, opens by demanding an answer: is virtue taught, acquired by practice, or inborn? Socrates turns the question until Meno says he has been numbed, then calls over one of Meno’s slaves and has the boy work out a geometry problem he was never taught. The question is what virtue is, and whether, if it is knowledge, anyone teaches it. No teachers can be found, so they leave it as true opinion given by divine lot, and Anytus goes off angry."),
        ("menexenus",
         "c. 401 BC. Menexenus is thinking of a public career. The speech he hears narrates events down to the King’s Peace of 386, after Socrates’ death, so the date cannot be made fully consistent.",
         "Menexenus comes from the Council chamber, where a speaker is about to be chosen for the public funeral, and he tells Socrates he may stand for office himself. Socrates recites from memory a funeral speech he says Aspasia composed, teasing him for wanting the usual praise of the city. The question is what that official praise is worth. The speech runs through the wars in the received style, and Menexenus is left to hear the irony."),
        ("cratylus",
         "Date uncertain. Hermogenes and Cratylus argue over names. Some take a reference to the Euthyphro as placing this talk on that same morning in 399.",
         "Hermogenes, stung because Cratylus will not grant him a name that fits, draws Socrates into the quarrel. Cratylus insists that names belong to things by nature. Hermogenes says they are fixed by agreement, and Socrates tries etymology after etymology before turning on both of them. The question is whether the truth about things can be learned from their names. He concludes that names are imperfect images, so the things themselves have to be studied, and Cratylus leaves unconvinced."),
    ]),
    ("The trial and death, 399 BC", "Fixed by what the dialogues say about the next day", [
        ("theaetetus",
         "Spring 399 BC. Theodorus introduces Theaetetus. At the end Socrates must answer the indictment. Euclid reads the conversation aloud years later.",
         "Euclid of Megara reads aloud to Terpsion a conversation he once wrote out: Theodorus brought him the boy Theaetetus, and Socrates, who was about to answer Meletus, examined the boy as a midwife examines someone in labour. Theaetetus offers one account of knowledge after another, and Socrates shows each one miscarrying. The question is what knowledge is. Perception, true judgment, and true judgment with an account all fail. Socrates leaves for the King Archon’s porch and asks them to meet again the next day."),
        ("euthyphro",
         "399 BC. The porch of the King Archon, before the hearing of the indictment.",
         "On his way in to the hearing of Meletus’ charge, Socrates meets Euthyphro coming out of the same porch, on his way to prosecute his own father for homicide. Euthyphro is sure he knows what piety requires, and Socrates detains him in the hope of learning something he can use in court. The question is what piety is. What the gods love, care of the gods, and a part of justice each collapse, and Euthyphro remembers another engagement and leaves."),
        ("sophist",
         "399 BC. The day after the Theaetetus. Theodorus brings an Eleatic stranger, as he had promised.",
         "As promised the day before, Theodorus returns with Theaetetus and brings a stranger from Elea, a companion of Parmenides’ circle. They set out to trap the sophist by dividing arts, and every division produces an image-maker whose work seems to require saying what is not. The question is how false speech is possible at all. They argue that difference is a real kind, so a statement can be false, and the sophist is caught as someone who hides his own ignorance behind copies."),
        ("statesman",
         "399 BC. The same day as the Sophist, continued. The younger Socrates takes Theaetetus’ place.",
         "The same morning goes on, and the Eleatic stranger changes partners from Theaetetus to the younger Socrates. He hunts the statesman by dividing the herding arts, loses the trail in a myth of a reversed cosmos, and begins again from weaving and from due measure. The question is what knowledge separates the true ruler from the many who imitate him. The statesman is the weaver who binds courageous and moderate natures into one city, with or without the crowd’s consent."),
        ("apology",
         "399 BC. The trial before the Athenian jury.",
         "Socrates stands before the jury, with Meletus as the speaker and Anytus and Lycon behind the charge. He separates the old comic slander from the indictment now filed, tells of Chaerephon’s question to the oracle, and describes how he examined politicians, poets, and craftsmen. The question before the court is whether he corrupts the young and fails to recognise the city’s gods. He is condemned, will not name a real penalty, and after the death sentence tells them that a good person cannot be harmed."),
        ("crito",
         "399 BC. The prison, before dawn. The sacred ship from Delos has been sighted.",
         "Before dawn Crito comes into the prison, having won over the guard, because the ship from Delos has been sighted and the execution will follow at once. He has the money and the route ready, and he begs Socrates to escape for his friends’ sake and his children’s. The question is whether it would be just to leave against the city’s verdict. Socrates imagines the laws saying that by living in Athens he agreed to accept its judgments, and he decides to stay."),
        ("phaedo",
         "399 BC. The prison, on the day of Socrates’ death. Phaedo tells the story to Echecrates.",
         "In Phlius, Phaedo tells Echecrates of the last day in the prison: the friends found Socrates already freed of the chain, Xanthippe was sent home, and the talk continued until the officer brought the poison. Simmias and Cebes make him defend the hope that the soul survives, and only then does he bathe and send for his children. The question is whether a philosopher has reason to think the soul outlives the body. Arguments from opposites, recollection, and the forms are given, a myth of the earth is told, and he drinks and dies."),
    ]),
    ("Outside the story", "No dramatic date, or Socrates is not in the work", [
        ("philebus",
         "No dramatic date. Socrates talks with Protarchus and Philebus, and nothing in the scene fixes a year. A proposal that this is spoken in the prison is not the usual view.",
         "Socrates is already in dispute with Philebus, who hands his brief to Protarchus and then sits by, refusing to surrender pleasure. They agree to test, with examples, what condition of soul could make a human life a good one. The question is whether that life is pleasure, knowledge, or some mixture of the two. Neither alone will do. A measured mixture ranks above both, and knowledge of what is stands nearest the good."),
        ("hipparchus",
         "No dramatic date. Nothing in the text fixes a year. A connection with the herms of 415 is only a guess. Traditionally doubted.",
         "A companion has just dismissed someone as a lover of gain, and Socrates will not let the phrase pass. He tells the story of Hipparchus, son of Peisistratus, who set herms along the roads inscribed with pieces of wisdom, and he keeps the companion answering. The question is what the love of gain is, and who has it. The argument claims that everyone wants what benefits them, so the contrast between decent people and profiteers fails, and there the talk stops."),
        ("lovers",
         "No dramatic date. A schoolroom, with no historical marker. Traditionally doubted.",
         "Socrates steps into Dionysius’ school and finds two boys quarreling over a point of learning, their lovers looking on. He asks the lovers whether this thing the boys are imitating, philosophy, is fine, and one of them says it is a little knowledge of every art. The question is what the philosopher is supposed to know. Socrates answers that the dabbler is best at nothing, and the lover is left unsure what knowledge belongs to a free person."),
        ("cleitophon",
         "No dramatic date. A speech addressed to Socrates, with no settled year. Traditionally doubted.",
         "Cleitophon asks leave to review Socrates in his hearing, then delivers the speech while Socrates does not answer. He reports that he was stirred by the exhortations to justice, questioned the companions, and received only formulas that circled back to justice itself. The question he poses is what justice is, and how a person comes to have it, once the urging is over. No answer is offered, and he says he will go to Thrasymachus unless one appears."),
        ("minos",
         "No dramatic date. Socrates and a companion, and no occasion is given. Traditionally doubted.",
         "Socrates is talking with a companion who thinks “what is law?” can be answered in a sentence. He rejects the first replies and turns to Minos, asking whether the poets were right to call the Cretan king savage. The question is what law is, if it is not simply whatever a city believes. Socrates argues that law aims at discovering what is, praises Minos as instructed by Zeus, and the companion is still unsatisfied when the piece ends."),
        ("laws",
         "Socrates is not a character. An Athenian stranger walks in Crete with Clinias of Cnossus and the Spartan Megillus.",
         "An Athenian stranger, walking on Crete from Cnossus toward the cave of Zeus, falls in with Clinias and the Spartan Megillus, and the three spend the day in talk. Clinias at last admits that he has been chosen to frame laws for a new colony, and the Athenian supplies the plan. The question is how law can train citizens toward virtue, and not only toward victory in war. They design Magnesia down to marriage, property, and punishment, and leave a nocturnal council to guard that aim."),
        ("epinomis",
         "Socrates is not a character. The same three speakers as in the Laws, continuing that conversation. Usually thought not to be by Plato.",
         "The same three meet again, as they had agreed at the end of the Laws, to name the study still missing from the council’s education. The Athenian sets the ordinary arts aside one by one. The question is what knowledge would make those guardians both wise and pious. He answers that it is number, and the order of the heavens, understood as the visible work of soul."),
        ("letters",
         "Not a scene from Socrates’ life. Thirteen letters attributed to Plato, mostly to Dionysius II and to Dion, after 399. They are not all regarded as genuine.",
         "The collection is not a scene with Socrates. Thirteen letters, addressed mostly to Dionysius II and to Dion, mix political advice, rebuke, and autobiography from the years after the trial. The Seventh, the letter most often defended as Plato’s, tells of the visits to Syracuse and of the failure to make a tyrant into a philosopher. The question in the political letters is whether a city can be reformed by someone who will not flatter its ruler. Several of the short letters are widely taken to be later exercises."),
    ]),
]


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def love_box(slug: str) -> str:
    """Box placed above the Greek on a dialogue page. No link onward."""
    return (
        '<aside class="love-box">'
        '<h2>Love in this dialogue</h2>'
        f'<p>{esc(LOVE[slug])}</p>'
        '</aside>'
    )


def story_box(slug: str) -> str:
    """Collapsed retelling, above the love box and the Greek."""
    return (
        '<details class="story-box">'
        '<summary>The story</summary>'
        f'<p>{esc(STORY[slug])}</p>'
        '</details>'
    )


def _year(when: str) -> str:
    """The date at the head of the setting line: "c. 432 BC", "399 BC"."""
    m = re.match(r"((?:c\. )?\d+(?:–\d+)? BC)", when)
    return m.group(1) if m else ""


def _row(slug: str, when: str, summary: str, href: str, greeks: dict[str, str]) -> str:
    greek = greeks.get(slug, GREEK[slug])
    year = _year(when)
    return (
        f'<a class="work" href="{esc(href)}">'
        f'<span class="names"><span class="en">{esc(ENGLISH[slug])}</span>'
        f'<span class="gk" lang="grc">{esc(greek)}</span></span>'
        f'<span class="desc">{esc(short_line(slug))}</span>'
        + (f'<span class="when">{esc(year)}</span>' if year else "")
        + '</a>'
    )


def _by_slug() -> dict[str, tuple[str, str]]:
    found = {}
    for _title, _blurb, items in PHASES:
        for slug, when, summary in items:
            found[slug] = (when, summary)
    return found


# One-line description for the catalogue, in the manner of a library listing:
# the question each dialogue asks, taken from its summary. Works whose summary
# names no single question get a line of their own.
SHORT = {
    "apology": "Socrates’ defence before the Athenian jury, and his words after the verdict.",
    "critias": "The tale of ancient Athens and Atlantis, broken off as Zeus begins to speak.",
    "cleitophon": "A complaint that Socrates urges virtue but never says what it is.",
    "letters": "Thirteen letters under Plato’s name, most of them about Syracuse.",
}


def short_line(slug: str) -> str:
    if slug in SHORT:
        return SHORT[slug]
    summary = _by_slug()[slug][1]
    m = re.search(r"The question (?:is|that remains is) ([^.]*\.)", summary)
    if not m:
        raise SystemExit(f"no one-line description for {slug}")
    line = m.group(1)
    return line[0].upper() + line[1:]


def about_info(slug: str) -> dict[str, str]:
    """What the dialogue page shows under About This Text."""
    when, _summary = _by_slug()[slug]
    return {"when": when, "story": STORY[slug], "love": LOVE[slug], "short": short_line(slug)}


def life_html(href_for, greeks: dict[str, str]) -> str:
    parts = []
    for title, blurb, items in PHASES:
        rows = "".join(
            _row(slug, when, summary, href_for(slug), greeks)
            for slug, when, summary in items
        )
        parts.append(
            f'<section class="group"><h2>{esc(title)} '
            f'<span class="catdesc">({esc(blurb)})</span></h2>'
            f'<div class="works">{rows}</div></section>'
        )
    return "".join(parts)


def tetralogy_html(href_for, greeks: dict[str, str]) -> str:
    info = _by_slug()
    parts = []
    for numeral, blurb, slugs in TETRALOGIES:
        rows = "".join(
            _row(slug, info[slug][0], info[slug][1], href_for(slug), greeks)
            for slug in slugs
        )
        parts.append(
            f'<section class="group"><h2>Tetralogy {esc(numeral)} '
            f'<span class="catdesc">({esc(blurb)})</span></h2>'
            f'<div class="works">{rows}</div></section>'
        )
    return "".join(parts)


NOTE = (
    "The dates are dramatic dates: the year of the conversation in the story, "
    "not the year Plato wrote the dialogue. The frame follows Debra Nails, "
    "The People of Plato (Indianapolis: Hackett, 2002), and the case for reading "
    "in dramatic order made by Catherine H. Zuckert, Plato’s Philosophers "
    "(Chicago: University of Chicago Press, 2010). The run from the Theaetetus "
    "to the Phaedo is fixed by what those dialogues say about the next day and "
    "the trial. The conventional setting of the Gorgias in 427 is that of "
    "E. R. Dodds, Plato: Gorgias (Oxford: Clarendon Press, 1959). For the "
    "Republic, see Debra Nails, “The Dramatic Date of Plato’s Republic,” "
    "Classical Journal 93 (1998). Where a year is still disputed, the more "
    "usual placement is printed and the alternative is named on the row. "
    "Narrower dates in the war years also use the internal evidence as set out "
    "by Christopher Planeaux."
)


def catalog_document(where: str, greeks: dict[str, str] | None = None) -> str:
    """where is 'plato' (files live in plato/) or 'texts' (files live in texts/)."""
    greeks = greeks or GREEK
    if where == "plato":
        href_for = lambda slug: f"{slug}.html"
        css = "../texts/library.css"
        icon = "../"
        brand = "../index.html"
        texts = "../texts/index.html"
        plato = "index.html"
        topics = "../index.html#topics"
        donate = "../index.html#donate"
        plato_current = ' aria-current="page"'
        home_reader = "../index.html#p-103"
    elif where == "texts":
        href_for = lambda slug: f"../plato/{slug}.html"
        css = "library.css"
        icon = "../"
        brand = "../index.html"
        texts = "../index.html"
        plato = "plato.html"
        topics = "../plato/alcibiades-1-annotated.html#topics"
        donate = "../plato/alcibiades-1-annotated.html#donate"
        plato_current = ' aria-current="page"'
        home_reader = "../plato/alcibiades-1-annotated.html#p-103"
    else:
        raise ValueError(where)

    life = life_html(href_for, greeks)
    tets = tetralogy_html(href_for, greeks)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="icon" href="{icon}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{icon}favicon.ico" sizes="any">
<link rel="icon" href="{icon}favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="{icon}apple-touch-icon.png">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plato · Sefarium</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400&amp;family=EB+Garamond:ital,wght@0,400;0,500;1,400&amp;family=Source+Sans+3:wght@400;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<nav class="sitebar" aria-label="Site">
  <a class="brand" href="{brand}"><span class="mark" aria-hidden="true">Ψ</span>Sefarium</a>
  <ul>
    <li><a href="{texts}">Texts</a></li>
    <li><a href="{plato}"{plato_current}>Plato</a></li>
    <li><a href="{topics}">Topics</a></li>
    <li><a href="{donate}">Donate</a></li>
  </ul>
</nav>
<div class="library">
  <main class="content" id="main">
    <div class="inner">
      <input class="ord" type="radio" name="order" id="ord-life" checked>
      <input class="ord" type="radio" name="order" id="ord-tet">
      <h1 class="cat-title">Plato</h1>
      <p class="cat-lead">The thirty-six works in the Perseus collection, in John Burnet’s Greek. The list follows the story of Socrates’ life. <span lang="grc">Πλάτων</span></p>
      <div class="viewtoggle">
        <label for="ord-life">Socrates’ life</label>
        <label for="ord-tet">Tetralogies</label>
      </div>
      <div class="order tet">
        {tets}
      </div>
      <div class="order life">
        {life}
      </div>
    </div>
  </main>
  <aside class="aside" aria-label="About">
    <section>
      <h2>About Plato</h2>
      <p>Plato (c. 428–348 BC) wrote dialogues in which Socrates, his teacher, questions the people of Athens about virtue, knowledge, love and the city. Thirty-six works come down under his name, some of them doubted since antiquity.</p>
      <p class="more"><a href="{home_reader}">Alcibiades I, with translation and commentary</a></p>
    </section>
    <section>
      <h2>About the order</h2>
      <p>“Socrates’ life” follows the order of the conversations in his life, not the order of writing. The year on each row is the dramatic date; each dialogue’s page gives the setting and the story.</p>
      <p>“Tetralogies” is Thrasyllus’ nine groups of four, the order transmitted with the corpus.</p>
      <p class="small">{esc(NOTE)}</p>
    </section>
    <section>
      <h2>Credits</h2>
      <p>Greek text of John Burnet, <cite>Platonis Opera</cite> (Oxford: Clarendon Press). Digital text: the <a href="https://www.perseus.tufts.edu/">Perseus Digital Library</a>, Tufts University.</p>
      <p>Licence: <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>. The same credit is on every dialogue page.</p>
    </section>
  </aside>
</div>
</body>
</html>
"""


def redirect_page(target: str, title: str) -> str:
    """A small page that forwards an old address, keeping any #fragment."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{target}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace("{target}" + location.hash);</script>
</head>
<body>
<p>This page has moved to <a href="{target}">{target}</a>.</p>
</body>
</html>
"""


def write_catalog_pages(root: Path, greeks: dict[str, str] | None = None) -> None:
    greeks = {**GREEK, **(greeks or {})}
    missing = [slug for slug in GREEK if slug not in _by_slug()]
    extra = [slug for slug in _by_slug() if slug not in GREEK]
    if missing or extra:
        raise SystemExit(f"catalogue mismatch missing={missing} extra={extra}")
    if set(LOVE) != set(GREEK) or set(STORY) != set(GREEK):
        raise SystemExit(
            f"story or love keys differ from works: "
            f"{(set(LOVE) | set(STORY)) ^ set(GREEK)}"
        )
    counts = {slug: len(text.split()) for slug, text in STORY.items()}
    over = {slug: n for slug, n in counts.items() if n > 300}
    if over:
        raise SystemExit(f"story over 300 words: {over}")
    prose = "\n".join(list(STORY.values()) + list(LOVE.values()))
    if "\u2014" in prose or "\u2013" in prose:
        raise SystemExit("catalogue prose contains an em dash or en dash")
    print("story word counts:")
    for slug, n in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"  {n:3}  {slug}")
    # One catalogue page; the old address forwards to it.
    (root / "plato" / "index.html").write_text(redirect_page("../texts/plato.html", "Plato · Sefarium"), encoding="utf-8")
    (root / "texts" / "plato.html").write_text(catalog_document("texts", greeks), encoding="utf-8")


def main() -> None:
    write_catalog_pages(Path(__file__).resolve().parents[1])
    print("wrote texts/plato.html (plato/index.html forwards to it)")


if __name__ == "__main__":
    main()
