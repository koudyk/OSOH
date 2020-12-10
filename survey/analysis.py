# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.3.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Analyzing the survey resulys

# +
from os import path
import copy
import warnings
import textwrap

import numpy as np
import pandas as pd
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

# %matplotlib inline

warnings.filterwarnings("ignore")
# -

# ## Load the survey results
# And delete the pilot data.
#
# We display the first row, with the column names. You'll see that this person filled it out in French, so there are NaN values for all the questions in English.
#
# If you scroll to the right, you can read all of the questions in the survey and see this participants' responses to the questions in French.

# +
survey = pd.read_csv("Doing Open Science in Grad School.csv", dtype=str)
##########################################
non_pilot_data = np.arange(7, len(survey))
survey = survey.iloc[non_pilot_data]
survey.reset_index(drop=True, inplace=True)
print("We have %d responses" % len(survey))

pd.set_option("display.max_columns", None)
survey.head(1)
# -

# # Before we analyze the data
# ## Let's shorten the column names & combine the English and French answers
# As you can see above, the column names are very long; they're the full questions that were asked in the survey. Also, participants had the option of completing the survey in English or French.
#
# Here, we load a file that contains
# - the variable name for each question
# - the English and French versions of each question
#
# And we'll look at the first 4 rows.

cols = pd.read_csv(
    "survey_column_names_and_translations.csv",
    index_col="variable_name",
    dtype=str,
)
cols.head(4)

# Now we'll use this information to convery the survey data into a simpler dataframe, with
# - variable names as columns (instead of the full questions), and
# - the English and French responses combined into one column per question (instead of there being 2 columns per question).

# +
df = pd.DataFrame(columns=list(cols.index))
for col in list(cols.index):
    en, fr = cols.loc[col]
    df[col] = survey[en].fillna(survey[fr])

################################
# df["language"] = df["language"].fillna("English")
# df = df[df["language"] == "English"]


df.head(1)
# -

# ## Let's create regex expressions for categorizing answers
#
# There are a few reasons for doing this:
# 1. to combine answers given in French and English. E.g., We'll replace "I don't know what this is" and "Je ne sais pas ce que c'est." with "dont_know".
# 2. for open ended questions, we might want to combine anwers that differ slightly but refer to a similar concept. E.g., the answers "McGill" or "mcgill university" will be replaced with "McGill".
# 3. for length multiple-choice answers, we want to replace them with a simple variable name with no spaces. E.g., "I don't know what this is" will be replaced with "dont_know".
#
# In all these dictionaries, the values are the regex expressions that will be used to search for text and replace it with the corresponding keys.
#

# +
uni_regexs = {
    "McGill University": "[Mm]c[Gg]ill",
    "Concordia University": "[Cc]oncordia",
    "Université de Montréal": "[Mm]ontr[eé]al|[Uu]de[Mm]",
    "Columbia University": "[Cc]olumbia",
}


level_regexs = {
    "Undergrad": "[Uu]ndergrad|bac",
    "Masters": "[Mm]aster|[Mm]aitrise",
    "Early PhD": "student|début",
    "Late PhD": "[Cc]andida",
    "Post-Doc": "([Pp]ost)([Dd]oc)",
    "Professor": "[Pp]rof",
}

dept_regexs = {
    "Neuro": "[Nn]euro|[Ii][Pp][Nn]",
    "Psych": "[Pp]sych",
    "Bio": "[Bb]io",
    "Engineering": "[Ee]ngineering",
    "Medical": "([Mm]edical|[Hh]ealth|[Ii]nfirm)",
    "Cognitive": "[Cc]ognit",
    "Education": "[Ed]ucat",
}

create_use_regexs = {
    "[blank]": "Non applicable",
    "dont_know": "I don't know what this is|Je ne sais pas ce que c'est",
    "never_used": "I've never used this|Je n'ai jamais utilisé cela",
    "have_used": "I've used this|J'ai utilisé ceci",
    "would_like_to_use": "I'd like to use this|J'aimerais pouvoir utiliser cela",
    "never_created": "I've never created this|Je n'ai jamais créé cela",
    "have_created": "I've created this|J'ai créé ceci",
    "would_like_to_create": "I'd like to create this|J'aimerais pouvoir créer cela",
}
# -

# # Descriptive visualization
#
# Now we'll visualize the answers.

# ## Participant background
# Here, we start by making a function for plotting the data from questions about the participant's background.

# +
matplotlib.rcParams.update({"font.size": 20})
df_cleaned = copy.deepcopy(df)


def plot_categorical_column(
    column, regex_dict, ax, title=" ", drop_other=False, plot_kind="barh"
):
    # if a cell contains a string that matches a regex item,
    # replace the cell contents with the regex key
    column = column.dropna()
    for key, regex_str in regex_dict.items():
        column[column.str.contains(regex_str, regex=True)] = key
    #         df_cleaned[column.str.contains(regex_str, regex=True)] = key

    # drop responses that can't be categorized with any of the keys
    keys = regex_dict.keys()
    if drop_other:
        for i, row in column.iteritems():
            if row not in keys:
                column = column.drop(i)

    # plot
    column.value_counts(normalize=True).sort_values().plot(
        kind=plot_kind, ax=ax
    )
    ax.set_title(title)
    #     ax.set_xlim((0, 1))
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_xticklabels([0, 50, 100])
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)


# +
fig, axs = plt.subplots(2, 2, figsize=(27, 12))

df["language"].value_counts(normalize=True).plot(
    kind="barh", title="Language used in the survey", ax=axs[0, 0]
)
axs[0, 0].set_xticks([0.0, 0.5, 1.0])
axs[0, 0].set_xticklabels([0, 50, 100])
# axs[0, 0].set_xlim((0, 1))
axs[0, 0].spines["right"].set_visible(False)
axs[0, 0].spines["top"].set_visible(False)

plot_categorical_column(
    df["level"],
    level_regexs,
    ax=axs[0, 1],
    title="Current level of training",
    plot_kind="barh",
)

# montreal_unis = [
#     "McGill University",
#     "Concordia University",
#     "Université de Montréal",
# ]
plot_categorical_column(
    df["university"],
    uni_regexs,
    ax=axs[1, 0],
    title="University",
    plot_kind="barh",
)

plot_categorical_column(
    df["department"],
    dept_regexs,
    ax=axs[1, 1],
    title="Department",
    plot_kind="barh",
)

plt.tight_layout()
plt.savefig("figures/participants_background.png", bbox_inches="tight")
# -

# ## Participants experience creating and using open-science objects
# Participants answered these two questions in a matrix of checkboxes, where
# - the rows were the open-science objects
# - the columns were their experience with them
#
# We'll visualize their answers as matrices as well.

# first, let's replace the full answers with simpler keywords
# E.g., "I don't know what this is" becomes "dont_know"
for key, regex_str in create_use_regexs.items():
    df_cleaned.replace(
        to_replace=regex_str,
        value=key,
        inplace=True,
        limit=None,
        regex=True,
        method="pad",
    )

# Let's create the matrix of counts of how many participants checked each box.

# +
create_use_keys = list(create_use_regexs.keys())
create_use_cols = [
    col for col in list(df.columns) if "create_" in col or "use_" in col
]
mat = pd.DataFrame(columns=create_use_cols, index=create_use_keys, dtype=int)

n_participants = len(df_cleaned)
for col in create_use_cols:
    for row in create_use_keys:
        mat.at[row, col] = (
            df_cleaned[col].str.contains(row).sum() / n_participants * 100
        )


mat[create_use_cols] = mat[create_use_cols].astype(int)


# -

# Visualization

# +
def ticklabels(var_list):
    return [
        s.replace("use_", "")
        .replace("create_", "")
        .replace("_", " ")
        .replace("each cit", "each / cit")
        for s in var_list
    ]


matplotlib.rcParams.update({"font.size": 24})
fig, axs = plt.subplots(1, 2, figsize=(27, 10))
vmax = 100
cmap = "viridis"
cbar = True
annot = True

create_cols = [col for col in list(mat.columns) if "create_" in col]
create_keys = [
    "dont_know",
    "never_created",
    "have_created",
    "would_like_to_create",
]
sns.heatmap(
    mat.loc[create_keys, create_cols].T,
    annot=annot,
    vmax=vmax,
    ax=axs[0],
    cbar=cbar,
    cmap=cmap,
    cbar_kws={"label": "% of participants"},
)
#     cbar_kws={'label': 'Number of participants'})
# axs[0].set_title("Experience CREATING open-science objects\n", fontsize=20)
axs[0].set_yticklabels(ticklabels(create_cols))
axs[0].set_xticklabels(ticklabels(create_keys), rotation=40, ha="right")

use_cols = [col for col in list(mat.columns) if "use_" in col]
use_keys = ["dont_know", "never_used", "have_used", "would_like_to_use"]
sns.heatmap(
    mat.loc[use_keys, use_cols].T,
    annot=annot,
    vmax=vmax,
    ax=axs[1],
    cbar=cbar,
    cmap=cmap,
    cbar_kws={"label": "% of participants"},
)
#             cbar_kws={'label': 'Number of participants'})
# axs[1].set_title("Experience USING open-science objects\n", fontsize=20)
axs[1].set_yticklabels(ticklabels(use_cols))
axs[1].set_xticklabels(ticklabels(use_keys), rotation=40, ha="right")

plt.tight_layout()
extent = (
    axs[0]
    .get_tightbbox(fig.canvas.renderer)
    .transformed(fig.dpi_scale_trans.inverted())
)
fig.savefig("figures/experience_creating.png", bbox_inches=extent)

extent = (
    axs[1]
    .get_tightbbox(fig.canvas.renderer)
    .transformed(fig.dpi_scale_trans.inverted())
)
fig.savefig("figures/experience_using.png", bbox_inches=extent)

plt.savefig("figures/experience.png", bbox_inches="tight")
# -

# ## Clustering types of participants

# +
# getting the data in the right format
to_encode = df_cleaned[create_use_cols].dropna()

one_hot_df = pd.DataFrame()
for column in list(to_encode.columns):
    for option in create_use_keys:
        one_hot_column = column + "__" + option
        for i_row, row in to_encode.iterrows():
            if option in row[column]:
                one_hot_df.at[i_row, one_hot_column] = True

one_hot_df = one_hot_df.fillna(False)
X = one_hot_df.to_numpy()

# +
import numpy as np
from sklearn.decomposition import PCA

n_components = 2
pca = PCA(n_components=n_components)
X = one_hot_df.to_numpy()
principalComponents = pca.fit_transform(X)

print("Explained variance ratio: ", pca.explained_variance_ratio_)

print("Singular values: ", pca.singular_values_)

pca_df = pd.DataFrame(data=principalComponents, columns=["PC 1", "PC 2"])

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlabel("PC 1")
ax.set_ylabel("PC 2")
ax.set_title("%d-component PCA" % n_components)
ax.scatter(
    pca_df["PC 1"], pca_df["PC 2"],
)
# -

# ## Barriers and desired resources

# +
barriers_options = {
    "Limited knowledge": [
        "Limited knowledge - I don't know how to make my resarch more open",
        "Connaissances limitées - Je ne sais pas comment je peux rendre ma recherche plus ouverte",
    ],
    "Limited skills": [
        "Limited skills - I don't have the skills to make my research more open (e.g., technical skills in data management or programming)",
        "Compétences limitées - Je n'ai pas les compétences nécessaires pour rendre ma recherche plus ouverte (par exemple, compétences techniques en gestion de données ou en programmation)",
    ],
    "Limited time": [
        "Limited time - I don't have time to learn/do open science",
        "Contrainte de temps - Je n'ai pas le temps d'apprendre ce qui est requis pour faire de la science ouverte",
    ],
    "Limited support": [
        "Limited support - My colleagues and/or supervisors don't think that open science is a priority",
        "Soutien limité - Mes collègues et/ou superviseurs ne pensent pas que la science ouverte soit une priorité",
    ],
    "Limited incentives": [
        "Limited incentives - I don't see any personal incentives to do open science",
        "Motivation limitées - Je ne vois aucune incitation personnelle à faire de la science ouverte",
    ],
    "Not convinced": [
        "Not convinced - I don't think that open science is important",
        "Pas convaincu.e - Je ne pense pas que la science ouverte soit importante/ je n'en comprends pas la pertience",
    ],
}

resources_options = {
    "Resource list": [
        "Resource list - A list of open resources that I can go through on my own time",
        "Liste de ressources - Une liste de ressources ouvertes pouvant être consultées lors de mes temps libres",
    ],
    "Tutorials": [
        "Tutorials - Short tutorials/discussions that I can attend online",
        "Tutoriels - Petits tutoriels/discussions auxquels je peux assister en ligne",
    ],
    "Office hours": [
        "Office hours - Regular office hours where I can get 1-on-1 guidance for doing open science, considering my specific research, skills, and resources",
        "Heures d'ouverture du bureau - Heures de bureau destinées à des fins d'encadrement/consultation pendant lesquelles je peux obtenir des conseils personnalisés pour faire de la science ouverte, en tenant compte de mes recherches, compétences et ressources spécifiques",
    ],
}

# +
matplotlib.rcParams.update({"font.size": 24})


def plot_categorical_column_with_comments(
    column,
    answer_options,
    ax,
    title=" ",
    plot_kind="barh",
    print_other_comments=True,
):

    # if a cell contains a string that matches a regex item,
    # replace the cell contents with the regex key
    column = column.dropna()
    keys = list(answer_options.keys())
    temp_df = pd.DataFrame(columns=keys)
    column = column.str.replace(
        "Heures de disponibilité / ", "Heures d'ouverture du bureau - "
    )
    temp_df["original_answer"] = column
    all_options = []
    for key, [en, fr] in answer_options.items():
        all_options.append(fr)
        all_options.append(en)

    for i, row in column.iteritems():
        for item in row.split(";"):
            for key, [en, fr] in answer_options.items():
                if item == en:
                    temp_df.at[i, key] = True
                if item == fr:
                    temp_df.at[i, key] = True
            if item not in all_options:
                temp_df.at[i, "Other"] = item
    temp_df[keys] = temp_df[keys].fillna(False)

    # plot
    to_plot = temp_df[keys].sum(axis=0) / len(temp_df) * 100
    to_plot.sort_values().plot(kind=plot_kind, ax=ax)
    #     ax.set_title(title + '\n')
    ax.set_xlim((0, 100))
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.set_xlabel("% of participants")

    # print other comments if desired
    if "Other" in list(temp_df.columns):
        if print_other_comments:
            other = []
            comments = list(temp_df["Other"].dropna())
            for s in comments:
                other = other + textwrap.wrap(s, width=70) + ["\n"]
            other = ["OTHER COMMENTS:\n\n"] + other
            other = "\n".join(other)
            other = other.replace("\n\n", "\n")
            props = dict(boxstyle="round", facecolor="whitesmoke", alpha=0.7)
            ax.text(
                1,
                0.85,
                other,
                fontsize=24,
                bbox=props,
                transform=plt.gcf().transFigure,
                verticalalignment="top",
            )


# +
fig, ax = plt.subplots(1, 1, figsize=(15, 9))
plot_categorical_column_with_comments(
    column=df["barriers"],
    answer_options=barriers_options,
    ax=ax,
    title="What barriers do you face when trying to do open science?",
    plot_kind="barh",
    print_other_comments=True,
)
fig.savefig("figures/barriers.png", bbox_inches="tight")

fig, ax = plt.subplots(1, 1, figsize=(15, 9))
plot_categorical_column_with_comments(
    df["resources_youd_like"],
    resources_options,
    ax=ax,
    title="What would help you make your research more open?",
    plot_kind="barh",
    print_other_comments=True,
)
fig.savefig("figures/resources_youd_like.png", bbox_inches="tight")

# -

# ## Would you be interested in applying to host Open Science Office Hours?

host_cols = ["host_paid", "host_volunteer"]
host_options = {"No": "No|Non", "Maybe": "Maybe|Peut", "Yes": "Yes|Qui"}
host_keys = list(host_options.keys())
host_mat = pd.DataFrame(columns=host_cols, index=host_keys)
for key, key_regex in host_options.items():
    for col in host_cols:
        host_mat.at[key, col] = (
            df[col].str.contains(key_regex, regex=True).sum()
            / n_participants
            * 100
        )
host_mat[host_cols] = host_mat[host_cols].astype(int)

# +
matplotlib.rcParams.update({"font.size": 18})
fig, ax = plt.subplots(figsize=(3, 3))

sns.heatmap(
    host_mat.T,
    annot=True,
    vmax=vmax,
    ax=ax,
    cbar=True,
    cmap=cmap,
    cbar_kws={"label": "% of participants"},
)
ax.set_title(
    "Would you be interested\nin applying to host\nOpen Science Office Hours?\n",
    fontsize=20,
)
ax.set_yticklabels(["As a paid\nteaching assistant", "As a volunteer"])
plt.tight_layout()
fig.savefig("figures/host.png", bbox_inches="tight")


# -

# ## Open-ended questions

# +
def all_answers_wordcloud(column, title="", language="all"):
    if language == "en":
        column = column[df["language"] == "English"]
    elif language == "fr":
        column = column[df["language"] == "Français"]

    column = column.dropna()

    # Concatenate the texts from all participants
    all_texts = ""
    for text in column:
        all_texts = all_texts + " " + str(text)

    # Create and generate a word cloud image:
    wordcloud = WordCloud().generate(all_texts)

    # Display the generated image:
    wordcloud = WordCloud(
        max_font_size=50, max_words=100, background_color="white"
    ).generate(all_texts)

    fig, ax = plt.subplots(figsize=(20, 10))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    #     plt.title(title + "\n", fontsize=40)
    plt.show()
    return fig, ax


# select language ('all', 'en', or 'fr')
language = "en"
fig, ax = all_answers_wordcloud(
    df["first_thoughts"],
    title='What do you think of when you hear the words "open science"?',
    language=language,
)
fig.savefig("figures/wc_first_thoughts.png", bbox_inches="tight")

fig, ax = all_answers_wordcloud(
    df["learn_next"],
    title="What would you like to learn about open science?",
    language=language,
)
fig.savefig("figures/wc_learn_next.png", bbox_inches="tight")


fig, ax = all_answers_wordcloud(
    df["motivation"],
    title="If you do open science,\nwhat motivates you to do so?",
    language=language,
)
fig.savefig("figures/wc_motivation.png", bbox_inches="tight")


fig, ax = all_answers_wordcloud(
    df["resources_that_helped"],
    title="If you do open science,\nwhat kinds of resources did you find most useful\nfor learning how to do open science?",
    language=language,
)
fig.savefig("figures/wc_resources_that_helped.png", bbox_inches="tight")