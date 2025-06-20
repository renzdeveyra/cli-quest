<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<nav class="bg-blue-600 text-white p-4">
	<div class="container mx-auto flex justify-between items-center">
		<a href="/" class="text-xl font-bold">CLI Quest</a>
		<div class="space-x-4">
			<a href="/challenges" class="hover:text-blue-200">Challenges</a>
			<a href="/demo/lucia" class="hover:text-blue-200">Demo</a>
		</div>
	</div>
</nav>

{@render children()}
