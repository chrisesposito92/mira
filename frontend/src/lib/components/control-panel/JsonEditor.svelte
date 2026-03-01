<script lang="ts">
	import { onDestroy } from 'svelte';
	import {
		EditorView,
		keymap,
		lineNumbers,
		highlightActiveLine,
		highlightSpecialChars,
		drawSelection,
		rectangularSelection,
	} from '@codemirror/view';
	import { EditorState } from '@codemirror/state';
	import { json } from '@codemirror/lang-json';
	import { lintGutter, linter, type Diagnostic } from '@codemirror/lint';
	import { oneDark } from '@codemirror/theme-one-dark';
	import { defaultKeymap, history, historyKeymap } from '@codemirror/commands';
	import {
		bracketMatching,
		foldGutter,
		foldKeymap,
		syntaxHighlighting,
		defaultHighlightStyle,
	} from '@codemirror/language';
	import { closeBrackets, closeBracketsKeymap } from '@codemirror/autocomplete';
	import { mode } from 'mode-watcher';

	let {
		value = '',
		readonly = false,
		onchange,
	}: {
		value: string;
		readonly?: boolean;
		onchange?: (value: string) => void;
	} = $props();

	let container: HTMLDivElement;
	let view: EditorView | undefined;

	const jsonLinter = linter((view) => {
		const diagnostics: Diagnostic[] = [];
		const doc = view.state.doc.toString();
		if (!doc.trim()) return diagnostics;
		try {
			JSON.parse(doc);
		} catch (e) {
			const msg = e instanceof Error ? e.message : 'Invalid JSON';
			diagnostics.push({
				from: 0,
				to: doc.length,
				severity: 'error',
				message: msg,
			});
		}
		return diagnostics;
	});

	function buildExtensions(isDark: boolean, isReadonly: boolean) {
		const extensions = [
			lineNumbers(),
			highlightActiveLine(),
			highlightSpecialChars(),
			drawSelection(),
			rectangularSelection(),
			history(),
			bracketMatching(),
			closeBrackets(),
			foldGutter(),
			json(),
			lintGutter(),
			jsonLinter,
			syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
			keymap.of([...defaultKeymap, ...historyKeymap, ...foldKeymap, ...closeBracketsKeymap]),
			EditorView.updateListener.of((update) => {
				if (update.docChanged) {
					onchange?.(update.state.doc.toString());
				}
			}),
		];
		if (isDark) extensions.push(oneDark);
		if (isReadonly) extensions.push(EditorState.readOnly.of(true));
		return extensions;
	}

	$effect(() => {
		if (!container) return;
		const isDark = mode.current === 'dark';

		if (!view) {
			view = new EditorView({
				state: EditorState.create({
					doc: value,
					extensions: buildExtensions(isDark, readonly),
				}),
				parent: container,
			});
		} else {
			const newState = EditorState.create({
				doc: view.state.doc.toString(),
				extensions: buildExtensions(isDark, readonly),
			});
			view.setState(newState);
		}
	});

	// Sync external value changes (e.g. selecting a different object)
	$effect(() => {
		if (view && value !== view.state.doc.toString()) {
			view.dispatch({
				changes: { from: 0, to: view.state.doc.length, insert: value },
			});
		}
	});

	onDestroy(() => {
		view?.destroy();
	});
</script>

<div bind:this={container} class="overflow-hidden rounded-md border"></div>
