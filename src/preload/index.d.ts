import type { BolhaAPI } from '../shared/types';
declare global { interface Window { bolha: BolhaAPI & { ready(): Promise<void> } } }
