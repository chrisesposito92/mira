<script lang="ts">
	import { enhance } from '$app/forms';
	import { Button } from '$lib/components/ui/button';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';

	let { form } = $props();
</script>

<Card.Root class="w-full max-w-sm">
	<Card.Header class="text-center">
		<Card.Title class="text-2xl font-bold tracking-tight">MIRA</Card.Title>
		<Card.Description>Create your account</Card.Description>
	</Card.Header>
	<Card.Content>
		{#if form?.success}
			<div class="space-y-4 text-center">
				<p class="text-sm text-muted-foreground">
					Check your email at <span class="font-medium text-foreground">{form.email}</span> to
					confirm your account.
				</p>
				<a href="/login" class="text-sm text-primary underline-offset-4 hover:underline">
					Back to login
				</a>
			</div>
		{:else}
			<form method="POST" use:enhance class="space-y-4">
				{#if form?.error}
					<div class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
						{form.error}
					</div>
				{/if}

				<div class="space-y-2">
					<Label for="full_name">Full name</Label>
					<Input
						id="full_name"
						name="full_name"
						type="text"
						placeholder="Jane Doe"
						value={form?.fullName ?? ''}
						required
					/>
				</div>

				<div class="space-y-2">
					<Label for="email">Email</Label>
					<Input
						id="email"
						name="email"
						type="email"
						placeholder="you@example.com"
						value={form?.email ?? ''}
						required
					/>
				</div>

				<div class="space-y-2">
					<Label for="password">Password</Label>
					<Input id="password" name="password" type="password" minlength={6} required />
				</div>

				<div class="space-y-2">
					<Label for="confirm_password">Confirm password</Label>
					<Input
						id="confirm_password"
						name="confirm_password"
						type="password"
						minlength={6}
						required
					/>
				</div>

				<Button type="submit" class="w-full">Create account</Button>
			</form>
		{/if}
	</Card.Content>
	{#if !form?.success}
		<Card.Footer class="justify-center">
			<p class="text-sm text-muted-foreground">
				Already have an account?
				<a href="/login" class="text-primary underline-offset-4 hover:underline">Sign in</a>
			</p>
		</Card.Footer>
	{/if}
</Card.Root>
