import React from 'react';
import logoIcon from '../assets/aspectLogoIcon.svg';
import background from '../assets/background.jpg';
import comboLogo from '../assets/Combo.png';
import { MicrosoftIcon } from '../components/common/MicrosoftIcon';

const Login = () => {
    const location = window.location;
    const error = new URLSearchParams(location.search).get('error');

    const handleLogin = (e) => {
        e.preventDefault();
        // Redirect to Backend Auth Endpoint
        window.location.href = "/api/auth/signin/microsoft";
    };

    const handleDevLogin = async (role, group = null, trade = null, region = null) => {
        try {
            await fetch("/api/auth/dev/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                    role,
                    assigned_group: group,
                    assigned_trade: trade,
                    assigned_region: region,
                }),
            });
            window.location.href = "/dashboard";
        } catch (err) {
            alert("Dev login failed: " + err.message);
        }
    };

    return (
        <div
            className="min-h-screen w-full flex items-center justify-center bg-cover bg-center bg-no-repeat relative overflow-hidden font-sans"
            style={{ backgroundImage: `url(${background})` }}
        >
            <div className="relative z-10 w-full max-w-[440px] px-6">
                <div className="bg-white rounded-[40px] shadow-[0_20px_50px_rgba(0,0,0,0.1)] p-8 flex flex-col items-center max-h-[90vh] overflow-y-auto">

                    {/* Logo */}
                    <div className="mb-6">
                        <img src={logoIcon} alt="Aspect Logo" className="w-[80px] h-auto" />
                    </div>

                    <div className="w-full space-y-6">
                        <div className="text-center space-y-2">
                            <h2 className="text-lg font-bold text-slate-800 tracking-tight">
                                Performance Summary
                            </h2>
                            <p className="text-xs text-slate-500 font-medium">
                                Sign in to access your bonus dashboard
                            </p>
                        </div>

                        {/* Microsoft Sign In Button */}
                        <button
                            onClick={handleLogin}
                            className="w-full group relative flex items-center justify-center gap-3 bg-[#f8fafc] hover:bg-[#27549D] border border-slate-200 hover:border-[#27549D] text-slate-700 hover:text-white font-bold py-3 px-6 rounded-2xl transition-all duration-300 shadow-sm hover:shadow-lg active:scale-[0.98]"
                        >
                            <div className="p-1 bg-white rounded-md shadow-sm group-hover:bg-white/90">
                                <MicrosoftIcon className="w-5 h-5" />
                            </div>
                            <span className="text-xs uppercase tracking-wider">
                                Login with Microsoft
                            </span>
                        </button>

                    </div>

                    {/* Developer Login */}
                    <div className="mt-6 w-full border-t border-slate-100 pt-4">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider text-center mb-3">
                            Test Roles (Dev)
                        </h3>
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                onClick={() => handleDevLogin("admin")}
                                className="px-3 py-2 text-[10px] font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded transition-colors"
                            >
                                Admin
                            </button>
                            <button
                                onClick={() => handleDevLogin("trade_group_manager", "HVac & Electrical")}
                                className="px-3 py-2 text-[10px] font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded transition-colors"
                            >
                                TGM (HVAC)
                            </button>
                            <button
                                onClick={() => handleDevLogin("trade_group_manager", "Plumbing & Drainage")}
                                className="px-3 py-2 text-[10px] font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded transition-colors"
                            >
                                TGM (P&D)
                            </button>
                            <button
                                onClick={() => handleDevLogin("regional_trade_group_manager", "Plumbing & Drainage", null, "North West")}
                                className="px-3 py-2 text-[10px] font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded transition-colors"
                            >
                                TGM (P&D, NW)
                            </button>
                            <button
                                onClick={() => handleDevLogin("trade_manager", "HVac & Electrical", "Electrical")}
                                className="px-3 py-2 text-[10px] font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded transition-colors"
                            >
                                TM (Electrical)
                            </button>
                        </div>
                    </div>

                    {/* Branding Footer */}
                    <div className="mt-12 flex flex-col items-center gap-2">
                        <span className="text-slate-400 text-[9px] font-bold uppercase tracking-[0.2em]">powered by:</span>
                        <img src={comboLogo} alt="Chumley Logo" className="h-4 w-auto opacity-70" />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
