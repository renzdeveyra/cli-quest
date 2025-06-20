<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Terminal } from '@xterm/xterm';
	import { FitAddon } from '@xterm/addon-fit';
	import { WebLinksAddon } from '@xterm/addon-web-links';
	import '@xterm/xterm/css/xterm.css';

	export let sessionId: string = '';
	export let onCommand: ((command: string) => void) | null = null;

	let terminalElement: HTMLDivElement;
	let terminal: Terminal;
	let fitAddon: FitAddon;
	let websocket: WebSocket | null = null;
	let currentLine = '';
	let isConnected = false;

	onMount(() => {
		// Initialize terminal
		terminal = new Terminal({
			cursorBlink: true,
			fontSize: 14,
			fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
			theme: {
				background: '#1e1e1e',
				foreground: '#d4d4d4',
				cursor: '#ffffff',
				selection: '#264f78'
			},
			cols: 80,
			rows: 24
		});

		// Add addons
		fitAddon = new FitAddon();
		terminal.loadAddon(fitAddon);
		terminal.loadAddon(new WebLinksAddon());

		// Open terminal in DOM element
		terminal.open(terminalElement);
		fitAddon.fit();

		// Handle terminal input
		terminal.onData((data) => {
			if (!isConnected) return;

			// Handle special keys
			if (data === '\r') {
				// Enter key - send command
				if (websocket && websocket.readyState === WebSocket.OPEN) {
					websocket.send(JSON.stringify({
						type: 'command',
						data: currentLine
					}));
					
					if (onCommand) {
						onCommand(currentLine);
					}
				}
				currentLine = '';
			} else if (data === '\u007f') {
				// Backspace
				if (currentLine.length > 0) {
					currentLine = currentLine.slice(0, -1);
					terminal.write('\b \b');
				}
			} else if (data === '\u0003') {
				// Ctrl+C
				if (websocket && websocket.readyState === WebSocket.OPEN) {
					websocket.send(JSON.stringify({
						type: 'interrupt',
						data: 'SIGINT'
					}));
				}
				currentLine = '';
			} else if (data.charCodeAt(0) >= 32) {
				// Printable characters
				currentLine += data;
				terminal.write(data);
			}
		});

		// Handle terminal resize
		terminal.onResize(({ cols, rows }) => {
			if (websocket && websocket.readyState === WebSocket.OPEN) {
				websocket.send(JSON.stringify({
					type: 'resize',
					cols,
					rows
				}));
			}
		});

		// Connect to WebSocket if sessionId is provided
		if (sessionId) {
			connectWebSocket();
		}

		// Handle window resize
		const handleResize = () => {
			fitAddon.fit();
		};
		window.addEventListener('resize', handleResize);

		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});

	onDestroy(() => {
		if (websocket) {
			websocket.close();
		}
		if (terminal) {
			terminal.dispose();
		}
	});

	function connectWebSocket() {
		if (!sessionId) return;

		const wsUrl = `ws://localhost:8000/api/terminal/${sessionId}`;
		websocket = new WebSocket(wsUrl);

		websocket.onopen = () => {
			isConnected = true;
			terminal.writeln('Connected to CLI Quest terminal...');
		};

		websocket.onmessage = (event) => {
			try {
				const message = JSON.parse(event.data);
				
				switch (message.type) {
					case 'output':
						terminal.write(message.data);
						break;
					case 'error':
						terminal.write(`\x1b[31m${message.data}\x1b[0m`); // Red text
						break;
					case 'clear':
						terminal.clear();
						break;
					default:
						console.log('Unknown message type:', message.type);
				}
			} catch (error) {
				console.error('Error parsing WebSocket message:', error);
				terminal.write(`\x1b[31mError: ${event.data}\x1b[0m`);
			}
		};

		websocket.onclose = () => {
			isConnected = false;
			terminal.writeln('\x1b[33mConnection closed. Attempting to reconnect...\x1b[0m');
			
			// Attempt to reconnect after 3 seconds
			setTimeout(() => {
				if (sessionId) {
					connectWebSocket();
				}
			}, 3000);
		};

		websocket.onerror = (error) => {
			console.error('WebSocket error:', error);
			terminal.writeln('\x1b[31mConnection error occurred.\x1b[0m');
		};
	}

	// Public methods
	export function writeToTerminal(text: string) {
		if (terminal) {
			terminal.write(text);
		}
	}

	export function clearTerminal() {
		if (terminal) {
			terminal.clear();
		}
	}

	export function focusTerminal() {
		if (terminal) {
			terminal.focus();
		}
	}

	// Reactive statement to handle sessionId changes
	$: if (sessionId && terminal) {
		connectWebSocket();
	}
</script>

<div class="terminal-container">
	<div bind:this={terminalElement} class="terminal"></div>
</div>

<style>
	.terminal-container {
		width: 100%;
		height: 100%;
		background-color: #1e1e1e;
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid #333;
	}

	.terminal {
		width: 100%;
		height: 100%;
		padding: 8px;
	}

	:global(.xterm) {
		height: 100% !important;
	}

	:global(.xterm-viewport) {
		overflow-y: auto;
	}
</style>
