<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { cn, snakeToTitle } from '$lib/utils.js';

	let { status, class: className }: { status: string; class?: string } = $props();

	const colorMap: Record<string, string> = {
		// Use case statuses
		draft: 'bg-muted text-muted-foreground border-transparent',
		in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-transparent',
		completed:
			'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-transparent',
		// Document statuses
		pending:
			'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 border-transparent',
		processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-transparent',
		ready: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-transparent',
		failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-transparent',
		// Connection statuses
		active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-transparent',
		inactive: 'bg-muted text-muted-foreground border-transparent',
		error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-transparent',
		// Object statuses
		approved: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-transparent',
		rejected: 'bg-muted text-muted-foreground border-transparent',
		pushed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-transparent',
		push_failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-transparent',
	};

	const labelMap: Record<string, string> = {
		in_progress: 'In Progress',
		push_failed: 'Push Failed',
	};

	const label = $derived(labelMap[status] ?? snakeToTitle(status));
	const colors = $derived(colorMap[status] ?? '');
</script>

<Badge variant="outline" class={cn(colors, className)}>{label}</Badge>
