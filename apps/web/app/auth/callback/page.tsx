"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

// Disable static generation for this dynamic OAuth callback page
export const dynamic = 'force-dynamic';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams?.get("token") ?? null;
  const error = searchParams?.get("error") ?? null;

  useEffect(() => {
    const handleCallback = async () => {
      if (error) {
        // Handle error case
        console.error("Authentication error:", error);
        setTimeout(() => {
          router.push("/login?error=authentication_failed");
        }, 3000);
        return;
      }

      if (token) {
        // Store token in localStorage (in production, use secure httpOnly cookies)
        localStorage.setItem("access_token", token);
        
        // Verify token by fetching user info
        try {
          const response = await fetch("/api/v1/auth/me", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const user = await response.json();
            localStorage.setItem("user", JSON.stringify(user));
            
            // Redirect to dashboard
            setTimeout(() => {
              router.push("/dashboard");
            }, 1500);
          } else {
            throw new Error("Invalid token");
          }
        } catch (err) {
          console.error("Token verification failed:", err);
          localStorage.removeItem("access_token");
          setTimeout(() => {
            router.push("/login?error=token_invalid");
          }, 3000);
        }
      } else {
        // No token or error, redirect to login
        router.push("/login");
      }
    };

    handleCallback();
  }, [token, error, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">
            {error ? "Authentication Failed" : token ? "Authentication Successful" : "Processing..."}
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          {error ? (
            <>
              <XCircle className="h-16 w-16 text-red-500 mx-auto" />
              <Alert variant="destructive">
                <AlertDescription>
                  Authentication failed. Redirecting to login page...
                </AlertDescription>
              </Alert>
            </>
          ) : token ? (
            <>
              <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto" />
              <p className="text-muted-foreground">
                Successfully authenticated! Redirecting to dashboard...
              </p>
            </>
          ) : (
            <>
              <Loader2 className="h-16 w-16 animate-spin text-primary mx-auto" />
              <p className="text-muted-foreground">
                Processing authentication...
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-center">Processing Authentication...</CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              <Loader2 className="h-16 w-16 animate-spin text-primary mx-auto" />
            </CardContent>
          </Card>
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}