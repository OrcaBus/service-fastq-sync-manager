/*
Interfaces for the application stacks
 */

export interface StatefulApplicationConfig {
  tableName: string;
}

export interface StatelessApplicationConfig {
  eventBusName: string;
  tableName: string;
}
