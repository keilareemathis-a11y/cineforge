import React from 'react';
import './LandingPage.css'; // Assume there are some CSS styles for layout

const LandingPage = () => {
    return (
        <div className="landing-page">
            <header className="hero">
                <h1>CineForge</h1>
                <p>Your gateway to discovering the best films, reviews, and community discussions!</p>
                <button className="cta-button">Get Started</button>
            </header>
            <section className="overview">
                <h2>Project Overview</h2>
                <p>CineForge is an innovative platform designed to enhance your movie-watching experience. Discover new films, share reviews, and connect with fellow movie enthusiasts. Our user-friendly interface and rich content make it easy for you to dive into the world of cinema.</p>
                <ul>
                    <li>Explore a vast library of films</li>
                    <li>Read and write detailed reviews</li>
                    <li>Join discussions with the community</li>
                    <li>Stay updated with the latest movie news</li>
                </ul>
            </section>
        </div>
    );
};

export default LandingPage;