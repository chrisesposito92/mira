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
		<Card.Description>Sign in to your account</Card.Description>
	</Card.Header>
	<Card.Content>
		<form method="POST" use:enhance class="space-y-4">
			{#if form?.error}
				<div class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
					{form.error}
				</div>
			{/if}

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
				<Input id="password" name="password" type="password" required />
			</div>

			<Button type="submit" class="w-full">Sign in</Button>
		</form>
	</Card.Content>
	<Card.Footer class="justify-center">
		<p class="text-sm text-muted-foreground">
			Don't have an account?
			<a href="/register" class="text-primary underline-offset-4 hover:underline">Sign up</a>
		</p>
	</Card.Footer>
</Card.Root>
