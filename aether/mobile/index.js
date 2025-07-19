/**
 * Aether Mobile Application Entry Point
 * @format
 */

import {AppRegistry} from 'react-native';
import App from './src/App';
import {name as appName} from './package.json';

// Register the main application component
AppRegistry.registerComponent(appName, () => App);