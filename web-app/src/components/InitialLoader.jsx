import React from 'react';
import logo from '../assets/Aspect_Logo.svg';
import './InitialLoader.css';

const InitialLoader = ({ text = "Initializing Dashboard" }) => {
    return (
        <div className="loader-overlay">
            <div className="loader-container">
                <img src={logo} alt="Aspect Logo" className="loader-logo" />
                <div className="flex flex-col items-center w-full gap-2">
                    <div className="loader-progress-wrapper">
                        <div className="loader-progress-bar"></div>
                    </div>
                    <span className="loader-text">{text}</span>
                </div>
            </div>
        </div>
    );
};

export default InitialLoader;
