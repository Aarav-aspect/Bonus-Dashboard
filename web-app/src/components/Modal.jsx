import React from 'react';
import ReactDOM from 'react-dom';
import { Card } from "@/components/ui/card"

const Modal = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;

    return ReactDOM.createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 modal-backdrop-enter">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Content */}
            <Card className="relative z-50 w-full max-w-4xl max-h-[90vh] overflow-y-auto border-border shadow-2xl p-6 bg-white rounded-3xl modal-card-enter" onClick={(e) => e.stopPropagation()}>
                <button
                    className="absolute right-4 top-4 rounded-full p-2 opacity-70 hover:opacity-100 hover:bg-muted transition-all cursor-pointer"
                    onClick={onClose}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                </button>

                {title && (
                    <h2 className="text-2xl font-black mb-6 text-foreground border-b border-border pb-4 tracking-tight">
                        {title}
                    </h2>
                )}
                <div className="py-2">
                    {children}
                </div>
            </Card>
        </div>,
        document.body
    );
};

export default Modal;
