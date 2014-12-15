DESIG
N:

The project is designed using object oriented principles, and following the guidelines of App Engine.
Each page is defined as a class instance, and rendered using Django templates. The page classes and their corresponding html templates are listed and described below:

- MainPage class, index.html: This is the main page for the application, which contains a list of the 10 most recent questions.
- QuestionDetail class, QuestionDetail.html: This is the "permalink" page for a given question, which displays the non-abbreviated version of a question.
- QuestionActivity class, QuestionActivity.html: This page displays a given question and all of the answers to that question
-UploadHandler class: This page processes the creation/edit of a question or answer, and then redirects to the appropriate page (usually the page that was previously accessed).
-Edit class, Edit.html: A page that allows you to edit a specified question or answer
-ProcessVote class: This page processes votes for both questions and answers. It then redirects to the previous page.
-AddFavorite class: This page processes requests to add or remove a "favorited" question. It then redirects to the previous page.
-FavoritesView class, FavoritesView.html: This page presents the list of favorited questions that the current user has selected.
-RSS class, RSS.xml: This page contains the RSS feed for a specified question. It is accessible from a <link> tag embedded in the <head> section of a given questions "Question Detail" or "Question Activity" page.

In addition to class instances for pages, classes are used to define datatypes for user generated content. This content is stored in the Datastore. These objects are defined as follows:

-Question class: This defines a question submitted by a user. Its parent is the "forum_key" which is a datastore root object that defines the forum.
-Answer class: This defines an answer submitted by a user. Its parent is a Question object.
-Vote class: This defines a user's vote. It's parent is either the Question or Answer object that the user has voted on.
-Favorites class: This defines Questions that are favorited by a given user.

FEATURES:

The project implements the following features:

-New questions can be submitted using the form at the bottom of the index page. New answers can be submitted at the bottom of the "QuestionActivity" page.
-The project supports users with the Google App Engine Python user API. There are "login" links in the upper right hand side of the main page. When a user is logged out, they have no ability to create or edit questions or answers, vote, or favorite questions.
-Users who have created a question or answer are allowed to edit them. "Edit Question" and "Edit Answer" links will appear below a question or answer if the user has created the item.
-Paging is implemented for the index page. 10 questions are displayed per page. Users can access next or previous pages by clicking the "next" or "prev" link at the bottom of the question list.
-Answers listed on the "QuestionActivity" page are sorted by the different between up and down votes, with the largest difference appearing first.
-Questions or answers can contain images. This can be accomplished by uploading the image when adding or editing a question or answer, or by adding a link to an image within the body of the question.
-URLs that are added to questions or answers are rendered as hyperlinks. This, as well as the rendering of images inline, is accomplished by a custom Django filter in the file "imagerender.py"
-Extra credit: A user can "favorite" certain questions, by clicking the "Add to Favorites" button below the question on the main page. The list of favorites is accessible via a link at the top right of the main page. Once a question is favorited, there is the option to remove it via a "Remove from Favorites" button where the add button formerly was.
