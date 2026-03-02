<script lang="ts">
	import { goto } from '$app/navigation';
	import * as Tabs from '$lib/components/ui/tabs';
	import * as Select from '$lib/components/ui/select';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import { Button } from '$lib/components/ui/button';
	import { Label } from '$lib/components/ui/label';
	import {
		UseCaseCard,
		CreateUseCaseDialog,
		FileUpload,
		EmptyState,
	} from '$lib/components/project';
	import { projectStore } from '$lib/stores';
	import {
		createApiClient,
		createProjectService,
		createUseCaseService,
		createDocumentService,
	} from '$lib/services';
	import { Plus, FileText, Briefcase, Settings, Trash2 } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import type { UseCaseCreate, OrgConnection } from '$lib/types';

	let { data } = $props();

	let createUcOpen = $state(false);
	let uploading = $state(false);
	let selectedConnectionId = $state('');
	let updatingConnection = $state(false);
	let deleteOpen = $state(false);
	let initialized = false;

	$effect(() => {
		projectStore.currentProject = data.project;
		projectStore.useCases = data.useCases;
		if (!initialized) {
			initialized = true;
			projectStore.documents = data.documents;
		}
		if (!updatingConnection) {
			selectedConnectionId = data.project.org_connection_id ?? '';
		}

		return () => {
			projectStore.currentProject = null;
			projectStore.useCases = [];
			projectStore.documents = [];
			projectStore.disconnectDocProcessing();
		};
	});

	function getServices() {
		const client = createApiClient(data.supabase);
		return {
			projectService: createProjectService(client),
			useCaseService: createUseCaseService(client),
			documentService: createDocumentService(client),
		};
	}

	async function handleCreateUseCase(formData: UseCaseCreate) {
		const { useCaseService } = getServices();
		const uc = await projectStore.createUseCase(useCaseService, data.project.id, formData);
		if (uc) {
			toast.success('Use case created');
		} else {
			toast.error(projectStore.error ?? 'Failed to create use case');
		}
	}

	async function handleUpload(file: File) {
		uploading = true;
		try {
			const { documentService } = getServices();
			const token = data.session!.access_token;
			const doc = await projectStore.uploadDocumentWithProgress(
				documentService,
				data.project.id,
				file,
				token,
			);
			if (doc) {
				toast.success(`Uploaded ${file.name}`);
			} else if (projectStore.error) {
				toast.error(projectStore.error);
			}
		} finally {
			uploading = false;
		}
	}

	async function handleDeleteDocument(id: string) {
		const { documentService } = getServices();
		const ok = await projectStore.deleteDocument(documentService, id);
		if (ok) toast.success('Document deleted');
		else toast.error(projectStore.error ?? 'Failed to delete');
	}

	async function handleConnectionChange(connId: string) {
		updatingConnection = true;
		const previousId = selectedConnectionId;
		selectedConnectionId = connId;
		try {
			const { projectService } = getServices();
			const result = await projectStore.updateProject(projectService, data.project.id, {
				org_connection_id: connId || null,
			});
			if (result) {
				toast.success('Connection updated');
			} else {
				selectedConnectionId = previousId;
				toast.error(projectStore.error ?? 'Failed to update connection');
			}
		} finally {
			updatingConnection = false;
		}
	}

	async function confirmDeleteProject() {
		const { projectService } = getServices();
		const ok = await projectStore.deleteProject(projectService, data.project.id);
		deleteOpen = false;
		if (ok) {
			toast.success('Project deleted');
			goto('/dashboard');
		} else {
			toast.error(projectStore.error ?? 'Failed to delete');
		}
	}

	function connectionLabel(connections: OrgConnection[], id: string): string {
		return connections.find((c) => c.id === id)?.org_name || 'None';
	}
</script>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight">{data.project.name}</h1>
		{#if data.project.customer_name}
			<p class="text-muted-foreground mt-1">{data.project.customer_name}</p>
		{/if}
		{#if data.project.description}
			<p class="text-muted-foreground mt-1 text-sm">{data.project.description}</p>
		{/if}
	</div>

	<Tabs.Root value="use-cases">
		<Tabs.List>
			<Tabs.Trigger value="use-cases">
				<Briefcase class="mr-1.5 size-4" />
				Use Cases
			</Tabs.Trigger>
			<Tabs.Trigger value="documents">
				<FileText class="mr-1.5 size-4" />
				Documents
			</Tabs.Trigger>
			<Tabs.Trigger value="settings">
				<Settings class="mr-1.5 size-4" />
				Settings
			</Tabs.Trigger>
		</Tabs.List>

		<!-- Use Cases Tab -->
		<Tabs.Content value="use-cases" class="mt-4">
			<div class="mb-4 flex items-center justify-between">
				<h2 class="text-lg font-semibold">Use Cases</h2>
				<Button size="sm" onclick={() => (createUcOpen = true)}>
					<Plus class="mr-1 size-4" />
					New Use Case
				</Button>
			</div>
			{#if projectStore.sortedUseCases.length === 0}
				<EmptyState
					icon={Briefcase}
					title="No use cases"
					description="Define billing use cases to configure m3ter entities."
					actionLabel="New Use Case"
					onaction={() => (createUcOpen = true)}
				/>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2">
					{#each projectStore.sortedUseCases as uc (uc.id)}
						<UseCaseCard useCase={uc} projectId={data.project.id} />
					{/each}
				</div>
			{/if}
		</Tabs.Content>

		<!-- Documents Tab -->
		<Tabs.Content value="documents" class="mt-4">
			<h2 class="mb-4 text-lg font-semibold">Documents</h2>
			<FileUpload
				documents={projectStore.documents}
				{uploading}
				uploadProgress={projectStore.uploadProgress}
				onupload={handleUpload}
				ondelete={handleDeleteDocument}
			/>
		</Tabs.Content>

		<!-- Settings Tab -->
		<Tabs.Content value="settings" class="mt-4 space-y-6">
			<div class="max-w-md space-y-4">
				<h2 class="text-lg font-semibold">Project Settings</h2>
				<div class="space-y-2">
					<Label>Org Connection</Label>
					<Select.Root
						type="single"
						value={selectedConnectionId}
						onValueChange={handleConnectionChange}
					>
						<Select.Trigger>
							{connectionLabel(data.connections, selectedConnectionId)}
						</Select.Trigger>
						<Select.Content>
							{#each data.connections as conn}
								<Select.Item value={conn.id}>{conn.org_name}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
			</div>

			<div class="border-destructive/50 max-w-md rounded-lg border p-4">
				<h3 class="text-destructive font-semibold">Danger Zone</h3>
				<p class="text-muted-foreground mt-1 text-sm">
					Permanently delete this project and all its data.
				</p>
				<Button variant="destructive" size="sm" class="mt-3" onclick={() => (deleteOpen = true)}>
					<Trash2 class="mr-1 size-4" />
					Delete Project
				</Button>
			</div>
		</Tabs.Content>
	</Tabs.Root>
</div>

<CreateUseCaseDialog bind:open={createUcOpen} oncreate={handleCreateUseCase} />

<AlertDialog.Root bind:open={deleteOpen}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete Project</AlertDialog.Title>
			<AlertDialog.Description>
				Are you sure? This will permanently delete the project and all its data. This action cannot
				be undone.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
			<AlertDialog.Action
				class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
				onclick={confirmDeleteProject}
			>
				Delete Project
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
