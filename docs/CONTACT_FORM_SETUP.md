# Contact form setup

ORCAST uses an optional [Formspree](https://formspree.io) endpoint for collaborator email capture on the landing and partners pages.

## Configure Formspree

1. Create a free Formspree form at https://formspree.io
2. Copy the form endpoint (e.g. `https://formspree.io/f/xxxxxxxx`)
3. Set `contactFormUrl` in the production environment file before building:

```typescript
// orcast-angular/src/environments/environment.aws.ts (and firebase.ts)
export const environment = {
  // ...
  contactFormUrl: 'https://formspree.io/f/YOUR_FORM_ID',
  contactEmail: 'contact@orcast.org'
};
```

Or inject at build time:

```bash
export FORMSPREE_URL="https://formspree.io/f/YOUR_FORM_ID"
sed -i '' "s|contactFormUrl: ''|contactFormUrl: '$FORMSPREE_URL'|" orcast-angular/src/environments/environment.aws.ts
```

## GitHub Actions

Add a repository variable `ORCAST_FORMSPREE_URL` and extend the inject step in `.github/workflows/firebase-hosting-merge.yml` and `cloudflare-deploy.yml` if you want CI builds to include the form.

## Fallback

When `contactFormUrl` is empty, the site shows a `mailto:contact@orcast.org` link. This works without any third-party service.

## Form fields

Both forms submit:

- `name`
- `email`
- `organization`
- `interest` (pilot / research / technical / other)
- `message`
- `_subject` (Formspree subject line)
