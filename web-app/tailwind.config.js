/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                brand: {
                    blue: "#27549D",
                    yellow: "#F1FF24",
                },
                support: {
                    gray: "#848EA3",
                    green: "#2EB844",
                    orange: "#F29630",
                    red: "#D15134",
                },
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: "#27549D", // Brand Blue
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                chart: {
                    '1': 'hsl(var(--chart-1))',
                    '2': 'hsl(var(--chart-2))',
                    '3': 'hsl(var(--chart-3))',
                    '4': 'hsl(var(--chart-4))',
                    '5': 'hsl(var(--chart-5))'
                }
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)',
                'xl': '1rem', // Original design often used 1rem (16px)
                '2xl': '1.5rem', // For larger cards
                '3xl': '2rem',
            },
            boxShadow: {
                'sm': '0 2px 8px -2px rgba(0, 0, 0, 0.05)', // Softer, more diffuse
                'md': '0 4px 12px -2px rgba(0, 0, 0, 0.08)', // Premium card lift
                'lg': '0 8px 24px -4px rgba(0, 0, 0, 0.12)', // High lift
            },
            fontFamily: {
                sans: ['Mont', 'sans-serif'],
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
}
