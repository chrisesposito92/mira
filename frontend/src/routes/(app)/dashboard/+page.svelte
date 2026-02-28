<script lang="ts">
	import { goto, invalidate } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { ProjectCard, CreateProjectDialog, EmptyState } from '$lib/components/project';
	import { projectStore } from '$lib/stores';
	import { createApiClient, createProjectService } from '$lib/services';
	import { Plus, FolderKanban } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import type { ProjectCreate } from '$lib/types';

	let { data } = $props();

	let createOpen = $state(false);

	$effect(() => {
		projectStore.projects = data.projects;
	});

	async function handleCreate(formData: ProjectCreate) {
		const client = createApiClient(data.supabase);
		const service = createProjectService(client);
		const project = await projectStore.createProject(service, formData);
		if (project) {
			toast.success('Project created');
			await invalidate('app:projects');
			goto(`/projects/${project.id}`);
		} else {
			toast.error(projectStore.error ?? 'Failed to create project');
		}
	}
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
			<p class="text-muted-foreground mt-1">Manage your m3ter billing configuration projects.</p>
		</div>
		<Button onclick={() => (createOpen = true)}>
			<Plus class="mr-2 size-4" />
			New Project
		</Button>
	</div>

	{#if projectStore.sortedProjects.length === 0}
		<EmptyState
			icon={FolderKanban}
			title="No projects yet"
			description="Create your first project to start configuring m3ter billing."
			actionLabel="New Project"
			onaction={() => (createOpen = true)}
		/>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each projectStore.sortedProjects as project (project.id)}
				<ProjectCard {project} onclick={() => goto(`/projects/${project.id}`)} />
			{/each}
		</div>
	{/if}
</div>

<CreateProjectDialog
	bind:open={createOpen}
	connections={data.connections}
	oncreate={handleCreate}
/>
