"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authClient } from "@/lib/auth-client";
import { useEffect, useState } from "react";

const Navbar: React.FC = () => {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      try {
        const session = await authClient.getSession();
        setIsLoggedIn(!!session.data);
      } catch {
        setIsLoggedIn(false);
      }
    };
    checkAuth();
  }, []);

  const handleLogout = async () => {
    await authClient.signOut({
      fetchOptions: {
        onSuccess: () => {
          setIsLoggedIn(false);
          router.push("/login");
        },
      },
    });
  };

  return (
    <nav className="w-full h-18 bg-white shadow-sm mb-4 rounded-b-lg border-b border-grayscale-border-subtle">
      <div className="flex flex-row justify-between items-center h-full px-4 py-4">
        {/* left: logo */}
        <div className="flex items-center">
          <Link href={isLoggedIn ? "/dashboard" : "/"} aria-label="Go to home">
            <Image
              src="/aspect-logo-primary.svg"
              alt="Aspect"
              width={140}
              height={36}
              priority
              className="cursor-pointer"
            />
          </Link>
        </div>

        {/* center: heading */}
        <h1 className="text-center text-xl font-bold text-grayscale-title">
          Dashboard
        </h1>

        {/* right: logout button (only shown when logged in) */}
        <div className="w-[100px]">
          {isLoggedIn ? (
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-darker rounded-md transition-colors"
            >
              Logout
            </button>
          ) : (
            <div className="w-[100px]" /> // Placeholder for layout consistency
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
