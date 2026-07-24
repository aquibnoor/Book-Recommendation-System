
import streamlit as st
import pandas as pd
import joblib

# -------------------------
# Page Configuration
# -------------------------

st.set_page_config(
    page_title="Book Recommendation System",
    page_icon="📚",
    layout="wide"
)

# -------------------------
# Load Files
# -------------------------

@st.cache_data
def load_data():

    active_data = pd.read_csv("active_data.csv")

    book_lookup = joblib.load("book_lookup.pkl")

    user_item_matrix = joblib.load("user_item_matrix.pkl")

    user_similarity_df = joblib.load("recommendation_model.pkl")

    return (
        active_data,
        book_lookup,
        user_item_matrix,
        user_similarity_df
    )


active_data, book_lookup, user_item_matrix, user_similarity_df = load_data()


# -------------------------
# Recommendation Function
# -------------------------

def recommend_books_for_user(
    user_id,
    top_n=10,
    top_similar_users=50,
    similarity_threshold=0.10
):

    if user_id not in user_item_matrix.index:
        return None

    similar_users = (
        user_similarity_df.loc[user_id]
        .sort_values(ascending=False)
        .iloc[1:top_similar_users + 1]
    )

    similar_users = similar_users[
        similar_users >= similarity_threshold
    ]

    if similar_users.empty:

        similar_users = (
            user_similarity_df.loc[user_id]
            .sort_values(ascending=False)
            .iloc[1:top_similar_users + 1]
        )

    user_books = user_item_matrix.loc[user_id]

    user_books = user_books[
        user_books > 0
    ].index

    recommendation_scores = {}

    for similar_user, similarity in similar_users.items():

        rated_books = user_item_matrix.loc[similar_user]

        rated_books = rated_books[
            rated_books > 0
        ]

        for isbn, rating in rated_books.items():

            if isbn in user_books:
                continue

            if isbn not in recommendation_scores:

                recommendation_scores[isbn] = {
                    "weighted_sum": 0,
                    "similarity_sum": 0
                }

            recommendation_scores[isbn]["weighted_sum"] += (
                rating * similarity
            )

            recommendation_scores[isbn]["similarity_sum"] += similarity

    recommendation_list = []

    for isbn, values in recommendation_scores.items():

        recommendation_score = (
            values["weighted_sum"]
            /
            values["similarity_sum"]
        )

        recommendation_list.append(
            [
                isbn,
                recommendation_score
            ]
        )

    recommendation_df = pd.DataFrame(
        recommendation_list,
        columns=[
            "ISBN",
            "Recommendation_Score"
        ]
    )

    recommendation_df = recommendation_df.merge(
        book_lookup,
        on="ISBN",
        how="left"
    )

    recommendation_df["Recommendation_Score"] = (
        recommendation_df["Recommendation_Score"]
        .round(2)
    )

    recommendation_df["Final_Score"] = (
        0.70
        *
        recommendation_df["Recommendation_Score"]
        +
        0.30
        *
        recommendation_df["Weighted_Rating"]
    )

    recommendation_df = (
        recommendation_df
        .sort_values(
            by="Final_Score",
            ascending=False
        )
        .drop_duplicates(
            subset="ISBN"
        )
    )

    return recommendation_df[
        [
            "Book-Title",
            "Book-Author",
            "Recommendation_Score",
            "Average_Book_Rating",
            "Weighted_Rating",
            "Final_Score",
            "Image-URL-M"
        ]
    ].head(top_n)


# -------------------------
# Sidebar
# -------------------------

st.sidebar.title("📚 Book Recommendation System")

st.sidebar.markdown("---")

st.sidebar.subheader("About")

st.sidebar.write(
    """
This project recommends books using

• User-Based Collaborative Filtering

• Cosine Similarity

• IMDb Weighted Rating
"""
)

st.sidebar.markdown("---")

st.sidebar.subheader("Dataset")

st.sidebar.write(f"Users : {active_data['User-ID'].nunique():,}")

st.sidebar.write(f"Books : {book_lookup['ISBN'].nunique():,}")

st.sidebar.write(f"Interactions : {len(active_data):,}")

st.sidebar.markdown("---")

st.sidebar.caption("Developed by Aquib Noor")

# -------------------------
# Main Page
# -------------------------

st.title("📚 Book Recommendation System")

st.caption(
    "Personalized recommendations using User-Based Collaborative Filtering"
)

st.markdown("---")

selected_user = st.selectbox(
    "Select User ID",
    sorted(active_data["User-ID"].unique())
)

st.write("")

recommend_button = st.button(
    "🔍 Recommend Books"
)

# -------------------------
# Recommendation Output
# -------------------------

if recommend_button:

    with st.spinner("Finding recommendations..."):

        recommendations = recommend_books_for_user(
            selected_user
        )

        if recommendations is None:

            st.error("User not found.")

        else:

            st.success("Top Recommended Books")

            st.write("")

            for _, row in recommendations.iterrows():

                col1, col2 = st.columns(
                    [1,4]
                )

                with col1:

                    st.image(
                        row["Image-URL-M"],
                        width=140
                    )

                with col2:

                    st.subheader(
                        row["Book-Title"]
                    )

                    st.write(
                        f"**Author:** {row['Book-Author']}"
                    )

                    st.write(
                        f"⭐ Average Rating : {row['Average_Book_Rating']:.2f}"
                    )

                    st.write(
                        f"🏆 Weighted Rating : {row['Weighted_Rating']:.2f}"
                    )

                    st.write(
                        f"🎯 Recommendation Score : {row['Recommendation_Score']:.2f}"
                    )

                    st.progress(
                        min(
                            row["Final_Score"]/10,
                            1.0
                        )
                    )

                st.markdown("---")

st.markdown("---")

st.caption(
    "Book Recommendation System using User-Based Collaborative Filtering | Streamlit"
)
