import { getSignUpUrl } from "@workos-inc/authkit-nextjs";
import { redirect } from "next/navigation";

// Account-creation entry point: redirect to the WorkOS AuthKit hosted sign-up page.
export async function GET() {
  redirect(await getSignUpUrl());
}
