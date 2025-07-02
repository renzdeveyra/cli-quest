<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	let terminalComponent: any = null;

	interface Challenge {
		id: string;
		title: string;
		description: string;
		difficulty: string;
		category: string;
		instructions: string;
		setup_files: Record<string, string>;
	}

	interface ChallengeSession {
		session_id: string;
		challenge_id: string;
		websocket_url: string;
		setup_files: Record<string, string>;
	}

	let challenge: Challenge | null = null;
	let session: ChallengeSession | null = null;
	let loading = true;
	let error = '';
	let flagInput = '';
	let submissionResult: { success: boolean; message: string; points: number } | null = null;
	let isSubmitting = false;
	let showFlagSubmission = false;

	const challengeId = $page.params.id;

	onMount(async () => {
		const Terminal = (await import('$lib/components/Terminal.svelte')).default;
		terminalComponent = Terminal;
		await loadChallenge();
	});

	async function loadChallenge() {
		try {
			// Load challenge details
			const challengeResponse = await fetch(`http://localhost:8000/api/challenges/${challengeId}`);
			if (!challengeResponse.ok) {
				throw new Error('Challenge not found');
			}
			challenge = await challengeResponse.json();

			// Start challenge session
			const sessionResponse = await fetch(`http://localhost:8000/api/challenges/${challengeId}/start`, {
				method: 'POST'
			});
			if (!sessionResponse.ok) {
				throw new Error('Failed to start challenge session');
			}
			session = await sessionResponse.json();

		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error occurred';
			console.error('Error loading challenge:', err);
		} finally {
			loading = false;
		}
	}

	async function submitFlag() {
		if (!flagInput.trim() || isSubmitting) return;

		isSubmitting = true;
		try {
			const response = await fetch(`http://localhost:8000/api/challenges/${challengeId}/submit`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ flag: flagInput.trim() })
			});

			if (response.ok) {
				submissionResult = await response.json();
			} else {
				submissionResult = {
					success: false,
					message: 'Failed to submit flag',
					points: 0
				};
			}
		} catch (err) {
			submissionResult = {
				success: false,
				message: 'Error submitting flag',
				points: 0
			};
		} finally {
			isSubmitting = false;
		}
	}

	function handleCommand(command: string) {
		console.log('Command executed:', command);
		// You can add command tracking logic here
	}

	function getDifficultyColor(difficulty: string): string {
		switch (difficulty.toLowerCase()) {
			case 'beginner':
				return 'bg-green-100 text-green-800';
			case 'intermediate':
				return 'bg-yellow-100 text-yellow-800';
			case 'advanced':
				return 'bg-red-100 text-red-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<svelte:head>
	<title>CLI Quest - {challenge?.title || 'Challenge'}</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
		</div>
	{:else if error}
		<div class="container mx-auto px-4 py-8">
			<div class="bg-red-50 border border-red-200 rounded-md p-4">
				<h3 class="text-lg font-medium text-red-800 mb-2">Error</h3>
				<p class="text-red-700">{error}</p>
				<button
					on:click={() => goto('/challenges')}
					class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
				>
					Back to Challenges
				</button>
			</div>
		</div>
	{:else if challenge && session}
		<div class="flex h-screen">
			<!-- Left Panel - Challenge Info -->
			<div class="w-1/3 bg-white border-r border-gray-200 overflow-y-auto">
				<div class="p-6">
					<div class="mb-4">
						<button
							on:click={() => goto('/challenges')}
							class="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
						>
							<svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L4.414 9H17a1 1 0 110 2H4.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
							</svg>
							Back to Challenges
						</button>
					</div>

					<div class="mb-6">
						<h1 class="text-2xl font-bold text-gray-900 mb-2">{challenge.title}</h1>
						<div class="flex items-center space-x-2 mb-4">
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getDifficultyColor(challenge.difficulty)}">
								{challenge.difficulty}
							</span>
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
								{challenge.category}
							</span>
						</div>
						<p class="text-gray-600">{challenge.description}</p>
					</div>

					<div class="mb-6">
						<h2 class="text-lg font-semibold text-gray-900 mb-3">Instructions</h2>
						<div class="bg-blue-50 border border-blue-200 rounded-md p-4">
							<p class="text-blue-800">{challenge.instructions}</p>
						</div>
					</div>

					{#if Object.keys(challenge.setup_files).length > 0}
						<div class="mb-6">
							<h2 class="text-lg font-semibold text-gray-900 mb-3">Setup Files</h2>
							<div class="space-y-2">
								{#each Object.keys(challenge.setup_files) as filename}
									<div class="bg-gray-50 border border-gray-200 rounded-md p-3">
										<code class="text-sm font-mono text-gray-800">{filename}</code>
									</div>
								{/each}
							</div>
						</div>
					{/if}

					<div class="mb-6">
						<button
							on:click={() => showFlagSubmission = !showFlagSubmission}
							class="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
						>
							Submit Flag
						</button>
					</div>

					{#if showFlagSubmission}
						<div class="mb-6">
							<div class="bg-gray-50 border border-gray-200 rounded-md p-4">
								<label for="flag" class="block text-sm font-medium text-gray-700 mb-2">
									Enter Flag:
								</label>
								<input
									id="flag"
									type="text"
									bind:value={flagInput}
									placeholder="CLI_QUEST_..."
									class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
								/>
								<button
									on:click={submitFlag}
									disabled={isSubmitting || !flagInput.trim()}
									class="mt-3 w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
								>
									{isSubmitting ? 'Submitting...' : 'Submit'}
								</button>
							</div>
						</div>
					{/if}

					{#if submissionResult}
						<div class="mb-6">
							<div class="border rounded-md p-4 {submissionResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}">
								<p class="text-sm font-medium {submissionResult.success ? 'text-green-800' : 'text-red-800'}">
									{submissionResult.message}
								</p>
								{#if submissionResult.points > 0}
									<p class="text-sm {submissionResult.success ? 'text-green-600' : 'text-red-600'} mt-1">
										Points: {submissionResult.points}
									</p>
								{/if}
							</div>
						</div>
					{/if}
				</div>
			</div>

			<!-- Right Panel - Terminal -->
			<div class="flex-1 bg-gray-900">
				<div class="h-full p-4">
					{#if terminalComponent && session}
						<svelte:component
							this={terminalComponent}
							sessionId={session.session_id}
							onCommand={handleCommand}
						/>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
