<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	interface Challenge {
		id: string;
		title: string;
		description: string;
		difficulty: string;
		category: string;
	}

	let challenges: Challenge[] = [];
	let loading = true;
	let error = '';

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:8000/api/challenges/');
			if (response.ok) {
				challenges = await response.json();
			} else {
				error = 'Failed to load challenges';
			}
		} catch (err) {
			error = 'Error connecting to server';
			console.error('Error loading challenges:', err);
		} finally {
			loading = false;
		}
	});

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

	function startChallenge(challengeId: string) {
		goto(`/challenges/${challengeId}`);
	}
</script>

<svelte:head>
	<title>CLI Quest - Challenges</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<div class="mb-8">
		<h1 class="text-4xl font-bold text-gray-900 mb-4">CLI Quest Challenges</h1>
		<p class="text-lg text-gray-600">
			Master the command line through interactive challenges. Each challenge teaches you essential CLI skills
			in a safe, sandboxed environment.
		</p>
	</div>

	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
		</div>
	{:else if error}
		<div class="bg-red-50 border border-red-200 rounded-md p-4">
			<div class="flex">
				<div class="flex-shrink-0">
					<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
					</svg>
				</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800">Error</h3>
					<div class="mt-2 text-sm text-red-700">
						<p>{error}</p>
						<p class="mt-1">Make sure the FastAPI backend is running on port 8000.</p>
					</div>
				</div>
			</div>
		</div>
	{:else if challenges.length === 0}
		<div class="text-center py-12">
			<h3 class="text-lg font-medium text-gray-900 mb-2">No challenges available</h3>
			<p class="text-gray-600">Check back later for new challenges!</p>
		</div>
	{:else}
		<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
			{#each challenges as challenge}
				<div class="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
					<div class="p-6">
						<div class="flex items-center justify-between mb-3">
							<h3 class="text-xl font-semibold text-gray-900">{challenge.title}</h3>
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getDifficultyColor(challenge.difficulty)}">
								{challenge.difficulty}
							</span>
						</div>
						
						<p class="text-gray-600 mb-4 line-clamp-3">{challenge.description}</p>
						
						<div class="flex items-center justify-between">
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
								{challenge.category}
							</span>
							
							<button
								on:click={() => startChallenge(challenge.id)}
								class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
							>
								Start Challenge
								<svg class="ml-2 -mr-1 w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
								</svg>
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.line-clamp-3 {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
