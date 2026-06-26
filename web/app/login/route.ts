import { getSignInUrl } from "@workos-inc/authkit-nextjs";
import { redirect } from "next/navigation";

// Sign-in entry point: redirect to the WorkOS AuthKit hosted sign-in page.
export async function GET() {
  redirect(await getSignInUrl());
}
